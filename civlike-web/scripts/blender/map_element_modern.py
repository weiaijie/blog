"""Small modern housing and hospital, with open stairwells and functional equipment."""
import math

from map_element_buildings import build_group, connection


def build(k, kind):
    hospital = kind == 'hospital'
    w, d, floors, storey = (10.2, 6.8, 2, 2.85) if hospital else (8.4, 6.6, 3, 2.70)
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = kind
    colors = {'concrete':'D8DCDA', 'plaster':'E4E3D8', 'accent':'46868C' if hospital else 'B66E59',
              'glass':'719FAE', 'frame':'394E54', 'roofing':'757E79', 'linen':'DDE5DD', 'blanket':'729999',
              'sign_blue':'316B9C', 'fan_blade':'C4CCCB'}
    for name, code in colors.items():
        material = k.M['wool'].copy(); material.name = 'modern_'+name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*linear, 1)
        k.M[name] = material

    def box(n, p, s, m='concrete', bevel=0): return k.box(n, p, s, m, bevel)
    def beam(n, a, b, r=.025, m='frame'): return k.beam(n, a, b, r, m, 8)
    def group(name, objects, start, full, anchor=(0, 0, 0), cover=False, **kwargs):
        if cover:
            for obj in objects: obj['inspectionCover'] = True
        return build_group(k, root, name, objects, start, full, anchor, **kwargs)

    def wall(name, horizontal, fixed, low, high, bottom, top, openings, start, material='plaster'):
        cuts = sorted(set([bottom, top]+[z for o in openings for z in o[2:] if bottom < z < top]))
        pieces = []
        for lo, hi in zip(cuts, cuts[1:]):
            spans = [(low, high)]; mid = (lo+hi)/2
            for a, b, c, e in openings:
                if c < mid < e:
                    spans = [(s, t) for x, y in spans for s, t in [(x, min(y, a)), (max(x, b), y)] if t-s > .001]
            for a, b in spans:
                p = ((a+b)/2, fixed, mid) if horizontal else (fixed, (a+b)/2, mid)
                size = (b-a, .16, hi-lo) if horizontal else (.16, b-a, hi-lo)
                pieces.append(box('wall_panel', p, size, material))
        group(name, pieces, start, start+.095)

    def window(horizontal, fixed, c, z, width=1.25, height=1.10):
        def panel(n, u, v, a, b, depth, mat):
            return box(n, (u, fixed, v) if horizontal else (fixed, u, v),
                       (a, depth, b) if horizontal else (depth, a, b), mat)
        parts = [panel('glazing', c, z, width-.07, height-.07, .035, 'glass')]
        for x in [c-width/2, c, c+width/2]: parts.append(panel('mullion', x, z, .045, height+.06, .095, 'frame'))
        for y in [z-height/2, z+height/2]: parts.append(panel('transom', c, y, width+.05, .045, .095, 'frame'))
        parts.append(panel('sill', c, z-height/2-.06, width+.16, .09, .28, 'concrete'))
        return parts

    def door(cx, y, floor, width=1.2, height=2.2, name='Entry'):
        hinge = -1 if cx < 0 else 1
        parts = [box('door_glass', (cx, y, floor+height/2), (width-.08, .045, height-.09), 'glass')]
        for x in [cx-width/2, cx+width/2]: parts.append(box('door_edge', (x, y, floor+height/2), (.04, .07, height), 'frame'))
        for z in [floor+.02, floor+height-.02]: parts.append(box('door_edge', (cx, y, z), (width, .07, .04), 'frame'))
        parts.append(beam('handle', (cx+hinge*width*.31, y-.06, floor+.95), (cx+hinge*width*.31, y-.06, floor+1.24), .018))
        node = group(name+'Door', parts, .78, .93, (cx-hinge*width/2, y, floor), motion='entry-door', axis=(0, 0, 1))
        node['doorAngle'] = hinge*math.pi/2

    def sliding_entry(y, floor, name):
        frame = [box('door_header', (0, y, floor+2.37), (1.93, .20, .18), 'frame')]
        for x in [-.88, .88]: frame.append(box('door_jamb', (x, y, floor+1.14), (.10, .20, 2.30), 'frame'))
        group(name+'Frame', frame, .70, .87)
        for side in [-1, 1]:
            x = side*.4
            pieces = [box('sliding_glass', (x, y, floor+1.15), (.76, .045, 2.20), 'glass')]
            for dx in [-.40, .40]: pieces.append(box('sliding_stile', (x+dx, y, floor+1.15), (.04, .07, 2.28), 'frame'))
            for z in [floor+.03, floor+2.27]: pieces.append(box('sliding_rail', (x, y, z), (.80, .07, .04), 'frame'))
            node = group(name+'SlidingDoor', pieces, .81, .96, (x, y, floor), motion='sliding-door', axis=(side, 0, 0))
            node['slideTravel'] = .86

    def bed(x, y, floor, clinical=False):
        parts = [box('bed_frame', (x, y, floor+.42), (1.04, 2.05, .12), 'frame'),
                 box('mattress', (x, y, floor+.54), (.97, 1.96, .16), 'linen', .025),
                 box('blanket', (x, y-.32, floor+.63), (.99, 1.12, .035), 'blanket'),
                 box('pillow', (x, y+.70, floor+.68), (.69, .35, .13), 'linen', .025)]
        for dx in [-.43, .43]:
            for dy in [-.86, .86]:
                parts.append(beam('bed_leg', (x+dx, y+dy, floor+.06), (x+dx, y+dy, floor+.40), .032))
                if clinical: parts.append(k.ico('caster', (x+dx, y+dy, floor+.06), (.055, .075, .06), 'frame', 2))
        for dy in [-1.03, 1.03]:
            parts.append(box('headboard' if dy > 0 else 'footboard', (x, y+dy, floor+.69), (1.03, .06, .42 if dy > 0 else .24), 'concrete' if clinical else 'wood'))
        if clinical:
            for dx in [-.55, .55]:
                parts.append(beam('safety_rail', (x+dx, y-.52, floor+.88), (x+dx, y+.48, floor+.88)))
                for dy in [-.52, .48]: parts.append(beam('rail_support', (x+dx, y+dy, floor+.45), (x+dx, y+dy, floor+.88), .016))
        return parts

    group('Foundation', [box('foundation', (0, 0, .08), (w+.4, d+.4, .16), 'concrete')], 0, .10)
    group('GroundFloor', [box('floor', (0, 0, .18), (w-.14, d-.14, .04), 'plaster')], .03, .12)
    if hospital:
        group('RearApron', [box('rear_apron', (0, 5.33, .10), (2.60, 4.26, .20))], .03, .12)
    ramp = [(-.8, -d/2, .20), (.8, -d/2, .20), (.8, -d/2-2.4, 0), (-.8, -d/2-2.4, 0),
            (-.8, -d/2, 0), (.8, -d/2, 0)]
    group('EntranceRamp', [k.mesh('entrance_ramp', ramp, [(0, 1, 2, 3), (0, 4, 5, 1), (4, 3, 2, 5), (0, 3, 4), (1, 5, 2)], 'concrete')], .05, .17)
    port = connection(k, root, 'Entrance', (0, -d/2-2.4, 0), 'pedestrian')
    port['normalGltf'] = [0, 0, 1]; port['clearWidth'] = 1.6
    roof = .2+floors*storey
    for level in range(floors):
        floor = .2+level*storey; start = .12+level*.19
        if level:
            plates = [box('floor_slab', (0, 0, floor-.08), (w-.16, d-.16, .16))] if hospital else [box('floor_slab', (side*(w/4+.65), 0, floor-.08), (w/2-1.30, d-.16, .16)) for side in [-1, 1]]
            group('UpperFloors', plates, start-.06, start+.02)
        entry_half = .81 if hospital else .61
        front_open = [(-entry_half, entry_half, floor, floor+(2.32 if hospital else 2.23))] if level == 0 else []
        windows = []
        for side in [-1, 1]:
            x = side*(3.30 if hospital else 2.75)
            if hospital or level == 0:
                front_open.append((x-.75, x+.75, floor+.86, floor+2.06))
                windows.extend(window(True, -d/2, x, floor+1.46, 1.50, 1.20))
            else:
                front_open.append((x-.62, x+.62, floor, floor+2.24))
                door(x, -d/2-.012, floor, name='Balcony')
            back_open = []
            for y in [-1.70, 1.70]:
                back_open.append((y-.67, y+.67, floor+.94, floor+2.04))
                windows.extend(window(False, side*w/2, y, floor+1.49, 1.34, 1.10))
            wall('SideWall', False, side*w/2, -d/2, d/2, floor, floor+storey-.16, back_open, start+.03)
        rear_centers = [-w*.33, w*.33] if hospital else [-w*.33, 0, w*.33]
        rear_open = [(x-.7, x+.7, floor+.94, floor+2.04) for x in rear_centers]
        for x in rear_centers: windows.extend(window(True, d/2, x, floor+1.49, 1.40, 1.10))
        if hospital:
            rear_open.append((-.81, .81, floor, floor+2.32))
            sliding_entry(d/2+.10, floor, 'Rear')
            if level:
                platform = [box('rear_platform', (0, 3.83, floor-.065), (2.60, 1.26, .13))]
                for side in [-1, 1]:
                    platform.append(beam('platform_rail', (side*1.26, 3.42, floor+.95), (side*1.26, 4.46, floor+.95)))
                    for cy in [3.45, 4.42]: platform.append(beam('platform_post', (side*1.26, cy, floor), (side*1.26, cy, floor+.95), .018))
                group('RearPlatform', platform, start+.04, start+.18)
        wall('FrontWall', True, -d/2, -w/2, w/2, floor, floor+storey-.16, front_open, start+.02, 'accent')
        wall('RearWall', True, d/2, -w/2, w/2, floor, floor+storey-.16, rear_open, start+.03)
        group('Windows', windows, start+.10, start+.22)
        bands = [box('floor_band', (0, side*d/2, floor+storey-.08), (w+.15, .22, .16)) for side in [-1, 1]]
        bands += [box('floor_band', (side*w/2, 0, floor+storey-.08), (.22, d+.15, .16)) for side in [-1, 1]]
        group('FloorBands', bands, start+.07, start+.18)
        first_y = -1.6 if hospital else -1.88
        landing_low, landing_high = -d/2+.08, first_y-.14
        room_entry = (landing_low+landing_high)/2
        group('FrontLanding', [box('landing', (0, room_entry, floor-.06), (2.60, landing_high-landing_low, .12))], start-.02, start+.06)
        for side in [-1, 1]:
            openings = [(room_entry-.60, room_entry+.60, floor, floor+2.23)]
            if hospital: openings.append((1.02, 2.22, floor, floor+2.23))
            wall('RoomPartition', False, side*1.30, -d/2+.1, d/2-.1, floor, floor+storey-.17, openings, start+.07)
            if hospital: wall('WardPartition', True, 0, side*1.3 if side > 0 else -w/2+.1, w/2-.1 if side > 0 else -1.3, floor, floor+storey-.17, [], start+.08)
        if level < floors-1:
            stairs = []; count = 8 if hospital else 9; rise = storey/(2*count)
            for flight in range(2):
                x = -.62 if flight == 0 else .62
                for step in range(count):
                    y = first_y+step*.28 if flight == 0 else .36-step*.28
                    top = floor+storey/2*flight+(step+1)*rise
                    stairs.append(box('stair_tread', (x, y, top-.035), (1.12, .28, .07), 'concrete'))
                y0, y1 = (first_y-.14, .50) if flight == 0 else (.50, first_y-.14)
                for dx in [-.57, .57]:
                    z0, z1 = floor+storey/2*flight, floor+storey/2*(flight+1)
                    stairs += [beam('stringer', (x+dx, y0, z0-.02), (x+dx, y1, z1-.02), .045),
                               beam('stair_rail', (x+dx, y0, z0+.92), (x+dx, y1, z1+.92))]
                    for step in [0, count//2, count-1]:
                        y = first_y+step*.28 if flight == 0 else .36-step*.28
                        z = floor+storey/2*flight+(step+1)*rise
                        stairs.append(beam('rail_post', (x+dx, y, z), (x+dx, y, z+.83), .018))
            stairs.append(box('half_landing', (0, .78, floor+storey/2-.06), (2.44, .56, .12)))
            if hospital:
                for obj in stairs: obj.location.y += 6.2
            group('SwitchbackStair', stairs, start+.07, start+.23)
        furniture = []
        for side in [-1, 1]:
            if hospital:
                for y in [-1.7, 1.7]:
                    x = side*3.40
                    if level == 0 and side == -1 and y < 0:
                        furniture += [box('reception_desk', (-2.18, -1.60, floor+.47), (.6, 1.25, .94), 'accent'),
                                      box('counter_top', (-2.18, -1.60, floor+.97), (.72, 1.35, .065), 'plaster')]
                        for cy in [-2.2, -1.4, -.6]:
                            furniture += [box('waiting_seat', (-4.10, cy, floor+.46), (.64, .61, .10), 'blanket'),
                                          box('seat_back', (-4.39, cy, floor+.81), (.07, .61, .68), 'blanket'),
                                          beam('seat_leg', (-4.10, cy, floor), (-4.10, cy, floor+.41), .04)]
                    else:
                        furniture.extend(bed(x, y, floor, True))
                        furniture += [box('bedside_cabinet', (x+side*.88, y+.54, floor+.36), (.55, .55, .72), 'concrete'),
                                      box('drawer_front', (x+side*.88, y+.245, floor+.45), (.46, .035, .24), 'accent'),
                                      beam('iv_pole', (x-side*.82, y+.60, floor), (x-side*.82, y+.60, floor+1.8), .014),
                                      beam('iv_hook', (x-side*.94, y+.60, floor+1.77), (x-side*.70, y+.60, floor+1.77), .011)]
            else:
                x = side*2.75; furniture.extend(bed(x, 1.7, floor))
                furniture += [box('wardrobe', (side*3.74, -.04, floor+1), (.62, 1.1, 2), 'wood_light'),
                              box('kitchen_cabinet', (side*1.75, 1.70, floor+.43), (.65, 1.65, .86), 'concrete'),
                              box('counter', (side*1.75, 1.70, floor+.90), (.70, 1.70, .08), 'frame'),
                              box('sofa_seat', (side*3.55, -1.68, floor+.42), (.68, 1.4, .28), 'blanket'),
                              box('sofa_back', (side*3.90, -1.68, floor+.71), (.12, 1.48, .64), 'blanket')]
                if level:
                    balcony = [box('balcony_deck', (x, -d/2-.48, floor-.07), (2.70, 1.0, .14))]
                    for dx in [-1.29, 1.29]: balcony.append(beam('balcony_side', (x+dx, -d/2-.02, floor+.96), (x+dx, -d/2-.97, floor+.96)))
                    balcony.append(beam('balcony_rail', (x-1.29, -d/2-.97, floor+.96), (x+1.29, -d/2-.97, floor+.96)))
                    for j in range(9): balcony.append(beam('baluster', (x-1.28+j*.32, -d/2-.97, floor), (x-1.28+j*.32, -d/2-.97, floor+.96), .014))
                    group('Balcony', balcony, start+.10, start+.25)
        group('RoomFurniture', furniture, .68+level*.025, .84+level*.025)

    if hospital:
        sliding_entry(-d/2-.16, .20, 'Entry')
        canopy = [box('entry_canopy', (0, -d/2-.88, 2.75), (3.35, 1.98, .15), 'accent')]
        for x in [-1.55, 1.55]: canopy.append(beam('canopy_column', (x, -d/2-1.64, 0), (x, -d/2-1.64, 2.70), .06))
        group('Canopy', canopy, .71, .88)
        sign = [box('hospital_sign', (0, -d/2-.16, 4.32), (1.18, .12, 1.14), 'sign_blue')]
        for x in [-.28, .28]: sign.append(box('H_upright', (x, -d/2-.235, 4.32), (.14, .04, .76), 'linen'))
        sign.append(box('H_crossbar', (0, -d/2-.235, 4.32), (.57, .04, .13), 'linen'))
        group('HospitalSign', sign, .88, .99)
    else:
        door(0, -d/2-.025, .20)
        group('EntryCanopy', [box('entry_canopy', (0, -d/2-.48, 2.57), (2.15, 1.06, .12), 'frame')], .76, .92)

    roof_parts = [box('roof_slab', (0, 0, roof-.065), (w+.2, d+.2, .13), 'roofing')]
    for side in [-1, 1]:
        roof_parts += [box('parapet', (0, side*d/2, roof+.20), (w+.2, .18, .40)),
                       box('parapet', (side*w/2, 0, roof+.20), (.18, d+.2, .40))]
    group('Roof', roof_parts, .73, .87, cover=True)
    for x in [-2.15, 2.15] if hospital else [0]:
        y = .3
        case = [box('vent_case', (x, y, roof+.32), (1.26, 1.26, .60), 'concrete'),
                box('vent_shadow', (x, y, roof+.635), (.95, .95, .04), 'frame')]
        for i in range(6): case.append(box('vent_louver', (x-.50+i*.20, y-.648, roof+.30), (.025, .04, .38), 'frame'))
        for i in range(4): case.append(beam('guard_bar', (x-.42+i*.28, y-.48, roof+.76), (x-.42+i*.28, y+.48, roof+.76), .014))
        group('VentHousing', case, .82, .96, cover=True)
        fan = [k.ico('fan_hub', (x, y, roof+.69), (.10, .10, .06), 'frame', 2)]
        for i in range(5):
            a = i*math.tau/5
            points = [(x+.08*math.cos(a), y+.08*math.sin(a), roof+.68),
                      (x+.43*math.cos(a), y+.43*math.sin(a), roof+.70),
                      (x+.39*math.cos(a+.50), y+.39*math.sin(a+.50), roof+.70),
                      (x+.10*math.cos(a+.70), y+.10*math.sin(a+.70), roof+.68)]
            fan.append(k.mesh('extractor_blade', points, [(0, 1, 2, 3)], 'fan_blade'))
        group('VentRotor', fan, .86, .98, (x, y, roof+.69), cover=True, motion='spin', axis=(0, 0, 1), rate=3.6)
    upgrades = []
    for side in [-1, 1]:
        x = side*(w/2+.54)
        upgrades.append(box('garden_coping', (x, -.5, .18), (.78, 3.0, .36), 'concrete'))
        upgrades.append(box('planter_soil', (x, -.5, .375), (.66, 2.87, .04), 'earth'))
        for i in range(7): upgrades.append(k.ico('shrub', (x, -1.66+i*.40, .62), (.30, .29, .26+.04*(i % 2)), 'leaf' if i % 2 else 'leaf_light', 2))
    group('GardenUpgrade', upgrades, .88, .99, tier=2)
    scaffold = [beam('scaffold_post', (-w/2-.28, y, 0), (-w/2-.28, y, 2.7), .045, 'wood') for y in [-1, 1]]
    scaffold.append(box('scaffold_board', (-w/2-.28, 0, 1.8), (.45, 2.4, .06), 'wood_light'))
    group('Scaffold', scaffold, .16, .30, temporary=True)
    root['animationBoundsMin'] = [-w/2-1.05, -.03, -7.50 if hospital else -d/2-.30]
    root['animationBoundsMax'] = [w/2+1.05, roof+.85, d/2+2.50]
