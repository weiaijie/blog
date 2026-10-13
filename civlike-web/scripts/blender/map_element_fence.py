"""Mortised farm fence with a hinged gate and a lifting gravity latch."""
import math

import bpy

from map_element_buildings import build_group, connection


def build(k):
    root = k.pivot('BuildingRoot', (0, 0, 0), [])
    root['buildingType'] = 'fence'
    root['animationBoundsMin'] = [-3.37, -.02, -.42]
    root['animationBoundsMax'] = [3.37, 1.57, 1.88]

    def group(name, objects, start, end, **kwargs):
        return build_group(k, root, name, objects, start, end, **kwargs)

    # The outer rail end planes mate without duplicating a shared end post.
    for side in [-1, 1]:
        socket = connection(k, root, 'FenceEndLeft' if side < 0 else 'FenceEndRight', (side*3.36, 0, 0), 'fence')
        socket['connectionProfile'] = 'farm-rail-2-v1'
        socket['outward'] = [side, 0, 0]
        socket['railHeights'] = [.48, .96]
    for side in [-1, 1]:
        port = connection(k, root, 'GateEntry' if side < 0 else 'GateExit', (0, side*1.90, 0), 'pedestrian')
        port['clearWidth'] = 1.50
        port['clearHeight'] = 1.90

    posts = [-3.04, -.99, .99, 3.04]
    feet = []
    for x in posts:
        feet.append(k.box('stone_post_foot', (x, 0, .035), (.35, .34, .07), 'stone', .025))
        for side in [-1, 1]:
            feet.append(k.ico('ground_chip', (x+side*.14, side*.17, .045), (.065, .048, .04), 'stone_light'))
    group('Footings', feet, 0, .12)
    for index, x in enumerate(posts):
        parts = [k.box('square_oak_post', (x, 0, .72), (.22, .22, 1.40), 'wood', .018),
                 k.beam('pyramid_post_cap', (x, 0, 1.43), (x, 0, 1.53), .17, 'wood_light', 4, .025)]
        for z in [.48, .96]:
            parts.append(k.box('mortise_shadow', (x, -.114, z), (.13, .012, .13), 'wood_dark', .008))
            parts.append(k.beam('wooden_through_pin', (x, -.139, z), (x, .139, z), .022, 'wood_light', 8))
        group('Post', parts, .12+index*.025, .27+index*.025)

    for side in [-1, 1]:
        for index, z in enumerate([.48, .96]):
            group('Rail', [k.box('joined_rail', (side*2.185, 0, z), (2.35, .105, .105), 'wood_light', .007)],
                  .34+index*.12, .43+index*.12)
        group('DiagonalStay', [k.beam('bracing', (side*1.12, .075, .41), (side*3.04, .075, 1.04), .044, 'wood', 4)], .54, .63)
        for index in range(8):
            x = side*(1.24+index*.26)
            group('Picket', [k.box('picket_board', (x, .091, .81), (.14, .055, .95), 'wood', .009),
                             k.beam('picket_tip', (x, .091, 1.285), (x, .091, 1.36), .099, 'wood_light', 4, .003)],
                  .63+index*.02, .72+index*.02, tier=2)

    hinge = (-.86, -.15, .24)
    fixed = []
    for z in [.35, 1.14]:
        fixed += [k.box('hinge_anchor', (-.99, -.131, z), (.14, .04, .16), 'iron', .008),
                  k.beam('pintle_arm', (-.99, -.15, z), (-.86, -.15, z), .032, 'iron', 8),
                  k.beam('vertical_pintle', (-.86, -.15, z-.07), (-.86, -.15, z+.07), .024, 'iron', 10)]
    group('FixedHinges', fixed, .57, .68)
    leaf = []
    for z in [.34, 1.18]:
        leaf.append(k.box('gate_horizontal', (-.01, -.15, z), (1.70, .075, .105), 'wood_light', .010))
    for index in range(7):
        x = -.76+index*.25
        leaf.append(k.box('gate_board', (x, -.15, .76), (.16, .065, .85), 'wood', .009))
        for z in [.34, 1.18]:
            leaf.append(k.beam('gate_nail', (x, -.20, z), (x, -.181, z), .017, 'iron', 8))
    leaf.append(k.beam('compression_brace', (-.79, -.093, .35), (.78, -.093, 1.14), .043, 'wood_light', 4))
    for z in [.35, 1.14]:
        leaf.append(k.box('hinge_strap', (-.58, -.198, z), (.54, .032, .055), 'iron', .006))
    gate = group('GateLeaf', leaf, .66, .80, anchor=hinge, motion='swing-gate', axis=(0, 0, 1))
    gate['gateAngle'] = -math.pi/2

    latch = group('GravityLatch', [k.box('latch_bar', (.815, -.217, .83), (.29, .045, .042), 'iron', .005),
                                  k.ico('latch_grip', (.85, -.254, .83), (.044, .022, .034), 'wood_dark', 2)],
                  .81, .90, anchor=(.68, -.217, .83), motion='gate-latch', axis=(0, 1, 0))
    bpy.context.view_layer.update()
    world = latch.matrix_world.copy()
    latch.parent = gate
    latch.matrix_world = world
    catch = [k.box('catch_plate', (.99, -.143, .83), (.13, .032, .20), 'iron', .006),
             k.box('catch_shelf', (.951, -.211, .795), (.09, .14, .025), 'iron', .004),
             k.box('catch_hook', (.951, -.274, .815), (.09, .020, .055), 'iron', .004)]
    group('LatchCatch', catch, .81, .90)
    # End-grain and narrow split seams are geometric, not painted black stripes.
    details = []
    for x in posts:
        for offset, height in [(-.054, .52), (.04, .94)]:
            details.append(k.box('weathered_split', (x+offset, -.1115, height), (.006, .004, .19), 'wood_dark', 0))
    group('Weathering', details, .90, .97)
    group('TemporaryBraces', [k.beam('erection_brace', (x, .30, .02), (x, .08, .85), .035, 'wood_dark', 4) for x in posts], .10, .20, temporary=True)
