"""Modular rural buildings with construction groups and functional pivots."""
import math

from mathutils import Vector


def build(k, kind):
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    for name, code in {'plaster':'D9D8C8', 'slate':'596F78', 'siding':'9C6651',
                       'glass':'527C80', 'water':'578E9C', 'foam':'B6D3CF', 'canvas':'D6D4B6'}.items():
        mat = k.M['wool'].copy()
        mat.name = name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear, 1)
        k.M[name] = mat

    def group(name, objects, start, end, anchor=(0, 0, 0), tier=1, temporary=False, motion='', axis=(0, 1, 0), rate=1):
        node = k.pivot(name, anchor, objects)
        node.parent = root
        node['buildStart'], node['buildFull'] = start, end
        node['buildingTier'], node['buildingTemporary'] = tier, temporary
        node['buildingMotion'] = motion
        # Runtime extras are in the exported glTF Y-up basis.
        node['motionAxis'] = [axis[0], axis[2], -axis[1]]
        node['motionRate'] = rate
        return node

    def socket(name, pos, kind):
        node = k.pivot(name, pos, [])
        node.parent = root
        node['connectionKind'] = kind

    def foundation(w, d):
        parts = [k.box('foundation_slab', (0, 0, .11), (w, d, .22), 'stone', .03)]
        for i in range(2):
            for j in range(7):
                x = -w/2+w*(j+.5)/7
                for side in [-1, 1]:
                    parts.append(k.box('foundation_block', (x, side*(d/2-.08), .13+i*.16), (w/7-.025, .20, .145), 'stone_light' if j%3==0 else 'stone', .017))
        group('Foundation', parts, 0, .12)
        group('EntranceSteps', [k.box('step', (0, -d/2-.24, .08), (1.25, .62, .16), 'stone_light', .025)], .02, .13)
        socket('Entrance', (0, -d/2-.55, 0), 'road')

    def window(x, y, z, width=.58, height=.65):
        parts = [k.box('recess', (x, y, z), (width+.12, .06, height+.12), 'wood_dark'),
                 k.box('glass', (x, y-.04, z), (width-.05, .025, height-.04), 'glass', 0)]
        for dx in [-width/2, 0, width/2]:
            parts.append(k.box('mullion', (x+dx, y-.065, z), (.045, .06, height+.07), 'wood_light', .005))
        for dz in [-height/2, 0, height/2]:
            parts.append(k.box('transom', (x, y-.07, z+dz), (width+.1, .065, .045), 'wood_light', .005))
        parts.append(k.box('sill', (x, y-.12, z-height/2-.075), (width+.24, .24, .08), 'stone_light'))
        return parts

    def door(y, width, height, start=.62, double=False):
        parts = [k.box('door_recess', (0, y+.035, .3+height/2), (width+.12, .045, height+.10), 'wood_dark', 0)]
        for x in [-width/2-.07, width/2+.07]:
            parts.append(k.box('door_post', (x, y-.05, .3+height/2), (.12, .16, height+.16), 'wood_light'))
        parts.append(k.box('lintel', (0, y-.05, .35+height), (width+.25, .17, .16), 'wood_light'))
        group('DoorFrame', parts, start-.10, start)
        for side in [-1, 1] if double else [-1]:
            span = width/2 if double else width
            cx = side*width/4 if double else 0
            hinge = (side*width/2, y-.085, .3)
            parts = [k.box('door_plank', (cx-span/2+(i+.5)*span/6, y-.085, .3+height/2), (span/6-.012, .08, height), 'wood', .006) for i in range(6)]
            for dz in [.25, height-.25]:
                parts.append(k.box('hinge_strap', (cx, y-.14, .3+dz), (span*.84, .035, .06), 'iron', .005))
            parts.append(k.beam('door_brace', (cx-span*.4, y-.145, .52), (cx+span*.4, y-.145, .3+height-.20), .045, 'wood_light', 4))
            parts.append(k.ico('handle', (cx-side*span*.3, y-.17, .3+height*.5), (.045, .04, .045), 'iron', 2))
            group('DoorLeaf', parts, start, start+.09, hinge, motion='door', axis=(0, 0, 1), rate=side)

    def roof(w, d, eaves, rise, material='tile', tier=1, cx=0, cy=0):
        # Each overlapping tile course is a separately assembled solid shell.
        rows, columns = 6, 8
        for row in range(rows):
            parts = []
            for side in [-1, 1]:
                for col in range(columns):
                    y0 = cy-d/2+col*d/columns-.016
                    y1 = y0+d/columns+.032
                    t0, t1 = max(0, row/rows-.018), min(1, (row+1)/rows+.025)
                    x0, x1 = cx+side*w*.5*t0, cx+side*w*.5*t1
                    z0, z1 = eaves+rise*(1-t0)+.025, eaves+rise*(1-t1)+.025
                    verts = [(x0,y0,z0),(x1,y0,z1),(x1,y1,z1),(x0,y1,z0),
                             (x0,y0,z0-.065),(x1,y0,z1-.065),(x1,y1,z1-.065),(x0,y1,z0-.065)]
                    parts.append(k.mesh('overlapping_roof_tile', verts, [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)], material))
            group('RoofCourse', parts, .59+row*.035, .65+row*.035, (cx,cy,eaves), tier)
        group('RidgeAndFascia', [k.beam('ridge', (cx,cy-d/2,eaves+rise+.08),(cx,cy+d/2,eaves+rise+.08), .10, material, 6)]+
              [k.beam('fascia',(cx,cy+side*d/2,eaves+rise),(cx+s*w/2,cy+side*d/2,eaves),.08,'wood_dark',4) for side in [-1,1] for s in [-1,1]], .80,.88,(cx,cy,eaves),tier)

    if kind == 'windmill':
        foundation(3.1, 3.1)
        for level in range(9):
            z = .35+level*.48
            radius = 1.33-level*.055
            parts = []
            for i in range(12):
                a, b = (i+level%2*.5)*math.tau/12, (i+1+level%2*.5)*math.tau/12-.023
                inner = radius-.20
                spans = [(a,b)]
                if level<3:
                    opening_a,opening_b = math.pi*1.5-math.asin(.47/radius),math.pi*1.5+math.asin(.47/radius)
                    spans = [(left,right) for left,right in [(a,min(b,opening_a)),(max(a,opening_b),b)] if right>left]
                for left,right in spans:
                    verts = [(r*math.cos(angle),r*math.sin(angle),h) for h in [z,z+.455] for r in [inner,radius] for angle in [left,right]]
                    parts.append(k.mesh('tower_masonry',verts,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'stone_light' if i%4==0 else 'stone'))
            group('TowerCourse',parts,.10+level*.047,.18+level*.047,(0,0,z))
        cap = k.beam('octagonal_cap',(0,0,4.6),(0,0,5.65),1.07,'slate',10,.03)
        group('Cap',[cap],.60,.75,(0,0,4.6))
        door(-1.34,.78,1.35)
        group('UpperWindow',window(0,-1.08,3.0,.40,.61),.57,.68)
        center = Vector((0,-1.50,4.13))
        rotor = [k.beam('rotor_hub',center+Vector((0,.18,0)),center-Vector((0,.24,0)),.17,'wood_dark',10)]
        for arm in range(4):
            a = arm*math.tau/4+.18
            radial, tangent = Vector((math.sin(a),0,math.cos(a))),Vector((math.cos(a),0,-math.sin(a)))
            def p(r,t,depth=0): return center+radial*r+tangent*t+Vector((0,depth,0))
            rotor.append(k.beam('sail_spar',p(.15,0),p(2.16,0),.065,'wood_light',4))
            rotor.append(k.beam('outer_sail_rail',p(.57,.60),p(2.16,.60),.035,'wood',4))
            for n in range(8):
                r=.57+n*.222
                rotor.append(k.beam('sail_rib',p(r,-.03),p(r,.65),.025,'wood_light',4))
            rotor.append(k.mesh('cloth_sail',[tuple(p(r,t,-.018)) for r,t in [(.64,.04),(.64,.56),(2.1,.56),(2.1,.04)]],[(0,1,2,3)],'canvas'))
        group('WindRotor',rotor,.78,.94,tuple(center),motion='spin',rate=.70)
        group('MainShaft',[k.beam('shaft',(0,-1.45,4.13),(0,.55,4.13),.10,'iron',10)],.65,.78,(0,0,4.13),motion='spin',rate=.70)
        for side in [-1,1]:
            platform=[k.box('gallery',(side*1.40,0,2.06),(.58,2.65,.13),'wood')]
            for y in [-.75,.75]:
                platform.append(k.beam('gallery_brace',(side*.87,y,1.43),(side*1.62,y,2.0),.065,'wood_dark',4))
            for y in [-1.14,-.38,.38,1.14]:
                platform.append(k.box('railing_post',(side*1.63,y,2.40),(.075,.075,.62),'wood_dark'))
            platform.append(k.box('handrail',(side*1.63,0,2.73),(.09,2.68,.085),'wood_light'))
            group('Gallery',platform,.69,.85,(side*1.4,0,2.0),2)
    else:
        barn = kind=='barn'
        watermill = kind=='watermill'
        w,d = (4.4,4.6) if barn else (3.6,3.8) if watermill else (3.2,3.0)
        eaves,rise = (2.7,1.6) if barn else (2.7,1.35) if watermill else (2.35,1.15)
        foundation(w+.28,d+.25)
        opening = 1.9 if barn else .90
        for level in range(7):
            z=.35+(eaves-.35)*(level+.5)/7
            h=(eaves-.35)/7-.015
            parts=[k.box('wall_course',(side*(w/2-.09),0,z),(.18,d,h),'siding' if barn else 'plaster',.009) for side in [-1,1]]
            parts.append(k.box('back_wall',(0,d/2-.09,z),(w,.18,h),'siding' if barn else 'plaster',.009))
            if z<(.35+2.1 if barn else .35+1.65):
                span=(w-opening)/2
                for side in [-1,1]:
                    parts.append(k.box('front_wall',(side*(opening/2+span/2),-d/2+.09,z),(span,.18,h),'siding' if barn else 'plaster',.009))
            else:
                parts.append(k.box('front_header',(0,-d/2+.09,z),(w,.18,h),'siding' if barn else 'plaster',.009))
            group('WallCourse',parts,.12+level*.053,.20+level*.053,(0,0,z-h/2))
        frame=[]
        for x in [-w/2+.03,w/2-.03]:
            for y in [-d/2-.01,0,d/2+.01]:
                frame.append(k.box('timber_post',(x,y,eaves/2+.16),(.16,.16,eaves-.25),'wood_dark'))
        for y in [-d/2-.03,d/2+.03]:
            frame.append(k.box('tie_beam',(0,y,eaves-.08),(w+.12,.16,.18),'wood_dark'))
            for side in [-1,1]:
                frame.append(k.beam('gable_rafter',(side*w/2,y,eaves),(0,y,eaves+rise),.10,'wood_dark',4))
            frame.append(k.mesh('gable_infill',[(x,y+dy,z) for dy in [-.015,.105] for x,z in [(-w/2,eaves),(w/2,eaves),(0,eaves+rise)]],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'siding' if barn else 'plaster'))
        for y in [-d*.25,0,d*.25]:
            frame.append(k.box('roof_tie',(0,y,eaves-.045),(w,.11,.13),'wood_light'))
            for side in [-1,1]:
                frame.append(k.beam('interior_rafter',(side*w/2,y,eaves),(0,y,eaves+rise-.04),.065,'wood',4))
        group('TimberFrame',frame,.38,.60,(0,0,.3))
        roof(w+.55,d+.50,eaves,rise,'slate' if watermill else 'tile')
        door(-d/2-.03,opening,2.1 if barn else 1.65,double=barn)
        features=[]
        if barn:
            for y in [-d/2-.09,d/2+.09]:
                for n in range(6):
                    features.append(k.box('loft_louver',(0,y,eaves+.16+n*.1),(.72,.10,.065),'wood_light'))
            for x in [-w/2,w/2]:
                for y in [-1.1,1.1]:
                    features.append(k.beam('diagonal_brace',(x,y-.55,.50),(x,y+.55,2.45),.06,'wood_light',4))
        else:
            for side in [-1,1]: features.extend(window(side*w*.32,-d/2-.075,1.48,.51,.68))
            side_window=window(0,0,1.49,.68,.74)
            rotation = math.pi/2
            for obj in side_window:
                x,y,z=obj.location
                obj.location=(w/2+.055-y,x+.45,z)
                obj.rotation_euler.z=rotation
            features.extend(side_window)
        group('FacadeDetails',features,.71,.90)
        if kind=='cottage':
            chimney=[]
            for layer in range(7):
                chimney.append(k.box('chimney_course',(.76,.58,3.0+layer*.16),(.47,.50,.15),'stone_light' if layer%2 else 'stone',.015))
            chimney.append(k.box('chimney_cap',(.76,.58,4.13),(.63,.65,.12),'stone'))
            chimney.append(k.box('flue',(.76,.58,4.195),(.34,.38,.012),'wood_dark',0))
            group('Chimney',chimney,.80,.97,(.76,.58,2.9))
        annex=[]
        ax=w/2+.75
        for y in [-1.12,1.12]:
            annex.extend([k.box('canopy_post',(ax+.55,y,1.0),(.14,.14,2.0),'wood_dark'),k.beam('canopy_brace',(ax+.55,y,1.5),(ax+.1,y,2.0),.05,'wood_light',4)])
        annex.append(k.box('canopy_deck',(ax,0,.16),(1.65,2.65,.15),'wood'))
        for n in range(8):
            panel=k.box('lean_to_roof',(ax,-1.34+n*.38,2.04),(1.9,.41,.095),'slate' if watermill else 'tile')
            panel.rotation_euler.y=.15
            annex.append(panel)
        for y in [-.70,.15,.85]:
            annex.append(k.box('stored_crate',(ax,y,.43),(.48,.52,.46),'straw' if barn else 'wood_light',.04))
        if not watermill: group('StorageCanopy',annex,.55,.93,(ax,0,0),2)
        else:
            # The waterwheel occupies this side; use a rear storage bay instead.
            for obj in annex: obj.location += Vector((-ax,d/2+1.5,0))
            group('StorageBay',annex,.55,.93,(0,d/2+1.5,0),2)
        if watermill:
            center=Vector((w/2+.59,0,1.55))
            wheel=[]
            for side in [-1,1]:
                for i in range(16):
                    a,b=i*math.tau/16,(i+1)*math.tau/16
                    def rim(t): return center+Vector((side*.35,math.sin(t)*1.30,math.cos(t)*1.30))
                    wheel.append(k.beam('rim_segment',rim(a),rim(b),.07,'wood_dark',6))
                    if i%2==0: wheel.append(k.beam('wheel_spoke',center+Vector((side*.35,0,0)),rim(a),.065,'wood',4))
            for i in range(16):
                a=i*math.tau/16
                pos=center+Vector((0,math.sin(a)*1.28,math.cos(a)*1.28))
                paddle=k.box('paddle',pos,(.78,.26,.11),'wood_light',.012)
                paddle.rotation_euler.x=-a
                wheel.append(paddle)
            wheel.append(k.beam('wheel_axle',center+Vector((-.68,0,0)),center+Vector((.48,0,0)),.13,'iron',12))
            group('WaterWheel',wheel,.70,.91,tuple(center),motion='spin',axis=(1,0,0),rate=-.8)
            channel=[k.box('channel_bed',(center.x,0,.055),(1.2,5.6,.11),'stone',.01)]
            for side in [-1,1]: channel.append(k.box('channel_bank',(center.x+side*.63,0,.18),(.16,5.6,.35),'stone',.02))
            group('MillRace',channel,.02,.18)
            water=k.box('running_water',(center.x,0,.18),(1.10,5.5,.06),'water',0)
            group('WaterSurface',[water],.94,1)
            for i in range(5):
                ripple=k.box('current_crest',(center.x,0,.219),(.88,.055,.015),'foam',.004)
                node=group('Current',[ripple],.95,1,(center.x,0,.219),motion='flow',axis=(0,-1,0),rate=1)
                node['flowPhase']=i/5
            socket('ChannelInlet',(center.x,2.8,.18),'water')
            socket('ChannelOutlet',(center.x,-2.8,.18),'water')

    scaffold=[]
    scaffold_y=-1.85 if kind=='windmill' else -d/2-.48
    for x in [-1.5,1.5]:
        scaffold.append(k.box('scaffold_pole',(x,scaffold_y,1.1),(.09,.09,2.2),'wood_light'))
    for z in [.5,1.3,2.1]: scaffold.append(k.box('scaffold_plank',(0,scaffold_y,z),(3.2,.42,.07),'wood'))
    group('Scaffold',scaffold,.09,.24,temporary=True)
    return root
