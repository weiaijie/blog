"""Cast-metal electric street lantern, with an editable bulb and glazed frame."""
import math

from map_element_buildings import build_group, connection


def build(k):
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = 'street-lamp'
    root['animationBoundsMin'] = [-.72, 0, -.72]
    root['animationBoundsMax'] = [.72, 4.05, .72]
    for name, code in {'patina':'47665D', 'brass':'BAA363', 'bulb':'F5E5BA', 'pane':'ACC9C3'}.items():
        mat = k.M['iron'].copy()
        mat.name = name
        rgb = [int(code[i:i+2], 16)/255 for i in (0, 2, 4)]
        linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
        shader = mat.node_tree.nodes['Principled BSDF']
        shader.inputs['Base Color'].default_value = (*linear, 1)
        shader.inputs['Metallic'].default_value = .55 if name in ['patina', 'brass'] else 0
        shader.inputs['Roughness'].default_value = .38 if name in ['patina', 'brass'] else .25
        if name == 'pane':
            shader.inputs['Alpha'].default_value = .12
            mat.surface_render_method = 'DITHERED'
        if name == 'bulb':
            shader.inputs['Emission Color'].default_value = (1, .63, .22, 1)
            shader.inputs['Emission Strength'].default_value = 2
        k.M[name] = mat

    def group(name, parts, start, end, **kwargs):
        return build_group(k, root, name, parts, start, end, **kwargs)

    socket = connection(k, root, 'PavementAnchor', (0, 0, 0), 'street-furniture')
    socket['connectionProfile'] = 'pavement-at-grade-v1'
    socket['clearRadius'] = .72
    pavers = []
    for x in [-1, 0, 1]:
        for y in [-1, 0, 1]:
            pavers.append(k.box('paving_stone', (x*.46, y*.46, .055), (.448, .448, .11), 'stone_light' if (x+y)%2 else 'stone', .018))
    group('Foundation', pavers, 0, .12)
    base = [k.box('base_plate', (0, 0, .16), (.52, .52, .10), 'iron', .026),
            k.beam('plinth', (0, 0, .21), (0, 0, .63), .225, 'patina', 8, .17)]
    for x in [-.19, .19]:
        for y in [-.19, .19]:
            base.append(k.beam('anchoring_nut', (x, y, .20), (x, y, .25), .038, 'iron', 6))
            base.append(k.beam('bolt_tip', (x, y, .25), (x, y, .27), .014, 'brass', 8))
    group('BoltedBase', base, .12, .27)
    for index, (bottom, top, radius) in enumerate([(.63, 1.40, .126), (1.40, 2.10, .105), (2.10, 2.77, .087)]):
        parts = [k.beam('tapered_shaft', (0, 0, bottom), (0, 0, top), radius, 'patina', 12, radius*.82)]
        for rib in range(8):
            angle = rib*math.tau/8
            parts.append(k.beam('fluting', (math.cos(angle)*radius, math.sin(angle)*radius, bottom+.06),
                                (math.cos(angle)*radius*.86, math.sin(angle)*radius*.86, top-.05), .012, 'iron', 5))
        parts.append(k.beam('collar', (0, 0, bottom), (0, 0, bottom+.055), radius*1.16, 'brass', 12))
        group('ShaftSection', parts, .25+index*.095, .39+index*.095)
    def plinth_front(z):
        return -(.225-(z-.21)*.055/.42)
    hatch = k.box('access_hatch', (0, plinth_front(.46)-.012, .46), (.16, .03, .25), 'iron', .016)
    hatch.rotation_euler.x = -math.atan(.055/.42)
    door = [hatch]
    for z in [.37, .55]:
        front = plinth_front(z)
        door.append(k.beam('hatch_screw', (0, front-.038, z), (0, front-.026, z), .013, 'brass', 8))
    group('ServiceHatch', door, .53, .62)
    support = [k.beam('lantern_pedestal', (0, 0, 2.77), (0, 0, 2.92), .10, 'iron', 10, .26),
               k.box('lantern_floor', (0, 0, 2.96), (.61, .61, .10), 'patina', .025)]
    for x in [-.265, .265]:
        for y in [-.265, .265]:
            support.append(k.beam('frame_stanchion', (x, y, 3.01), (x, y, 3.57), .026, 'iron', 6))
    for side in [-1, 1]:
        for z in [3.015, 3.56]:
            support.append(k.box('glazing_bar', (side*.27, 0, z), (.035, .57, .03), 'brass', .005))
            support.append(k.box('glazing_bar', (0, side*.27, z), (.57, .035, .03), 'brass', .005))
    group('LanternFrame', support, .60, .74)
    glass = []
    for side in [-1, 1]:
        glass.append(k.mesh('side_glass', [(side*.263,-.24,3.04),(side*.263,.24,3.04),(side*.263,.24,3.535),(side*.263,-.24,3.535)], [(0,1,2,3)], 'pane'))
        glass.append(k.mesh('front_glass', [(-.24,side*.263,3.04),(.24,side*.263,3.04),(.24,side*.263,3.535),(-.24,side*.263,3.535)], [(0,1,2,3)], 'pane'))
    group('Glazing', glass, .74, .83)
    group('BulbSocket', [k.beam('ceramic_holder', (0, 0, 3.025), (0, 0, 3.15), .085, 'wool', 10),
                         k.beam('screw_base', (0, 0, 3.13), (0, 0, 3.21), .068, 'brass', 12)], .71, .81)
    emitter = group('LampEmitter', [k.ico('frosted_bulb', (0, 0, 3.31), (.115, .115, .15), 'bulb', 3)], .81, .89, anchor=(0, 0, 3.31))
    emitter['lampEmitter'] = True
    emitter['lampPower'] = 35
    emitter['lampRange'] = 5
    roof = [k.beam('hipped_cap', (0, 0, 3.60), (0, 0, 3.83), .47, 'patina', 4, .08),
            k.beam('vent_neck', (0, 0, 3.80), (0, 0, 3.94), .062, 'iron', 8),
            k.ico('finial', (0, 0, 3.965), (.067, .067, .068), 'brass', 2)]
    group('LanternRoof', roof, .84, .95)
    ornaments = []
    for side in [-1, 1]:
        points = [(side*(.10+.25*math.sin(i*math.pi/10)), 0, 2.58+i*.032) for i in range(11)]
        for a, b in zip(points, points[1:]):
            ornaments.append(k.beam('scroll_bracket', a, b, .022, 'iron', 6))
        ornaments.append(k.ico('bracket_tip', points[-1], (.04, .04, .04), 'brass', 2))
    group('ScrollBrackets', ornaments, .91, .98, tier=2)
