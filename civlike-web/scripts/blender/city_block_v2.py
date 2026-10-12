"""Reusable castle kit and a small-footprint capital tile. Blender 4.5."""
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
M = {}
RNG = random.Random(918)
DETAIL = True


def material(name, color, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = .72
    shader.inputs['Metallic'].default_value = metallic
    return mat


def palette():
    colors = {
        'stone': (.57, .52, .40), 'light': (.76, .70, .56),
        'shade': (.38, .36, .30), 'mortar': (.29, .28, .23),
        'blue': (.018, .12, .45), 'blue2': (.028, .23, .65),
        'blue3': (.035, .18, .53), 'gold': (.95, .57, .07),
        'wood': (.24, .105, .035), 'iron': (.065, .075, .075),
        'glass': (.018, .08, .12), 'grass': (.28, .43, .055),
        'grass2': (.37, .51, .07), 'grass3': (.22, .35, .04),
        'soil': (.25, .145, .065), 'earth': (.36, .235, .115),
        'path': (.58, .43, .22), 'water': (.018, .38, .58),
        'foam': (.32, .83, .87), 'pine': (.075, .25, .04),
        'pine2': (.19, .36, .045), 'wheat': (.83, .51, .035),
        'flower': (.95, .33, .19), 'flame': (1, .28, .015),
    }
    M.clear()
    M.update({k: material('capital_' + k, v, .35 if k == 'gold' else 0) for k, v in colors.items()})
    size = 256
    texture = bpy.data.images.new('capital_stone_albedo', width=size, height=size)
    pixels = []
    for y in range(size):
        row = y // 64
        for x in range(size):
            joint = y % 64 < 2 or (x + (row % 2) * 64) % 128 < 2
            shade = .80 if joint else 1 + .035 * math.sin(x * .09 + row * 7)
            pixels.extend([c * shade for c in colors['stone']] + [1])
    texture.pixels.foreach_set(pixels)
    texture.pack()
    texture.filepath_raw = str(ROOT / 'src/render/assets/textures/capital-v2-stone.png')
    texture.file_format = 'PNG'
    texture.save()
    node = M['stone'].node_tree.nodes.new('ShaderNodeTexImage')
    node.image = texture
    M['stone'].node_tree.links.new(node.outputs['Color'], M['stone'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'])


def mesh(name, verts, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    if all(edge.is_manifold for edge in bm.edges):
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(M[mat])
    return obj


def box(name, size, pos, mat='stone', bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(M[mat])
    if mat == 'stone':
        uv = obj.data.uv_layers.active
        for face in obj.data.polygons:
            axes = (1, 2) if abs(face.normal.x) > .5 else (0, 2) if abs(face.normal.y) > .5 else (0, 1)
            for loop in face.loop_indices:
                co = obj.data.vertices[obj.data.loops[loop].vertex_index].co
                uv.data[loop].uv = (co[axes[0]], co[axes[1]])
    if bevel and DETAIL:
        mod = obj.modifiers.new('cut_stone_edges', 'BEVEL')
        mod.width = min(bevel, min(size) * .17)
        mod.segments = 1
        obj.modifiers.new('weighted_corner_normals', 'WEIGHTED_NORMAL')
    return obj


def cone(name, radius, height, pos, mat, vertices=8):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=0, depth=height, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(M[mat])
    return obj


def polygon_prism(name, points, depth, y, mat):
    n = len(points)
    verts = [(x, y - depth / 2, z) for x, z in points] + [(x, y + depth / 2, z) for x, z in points]
    faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    return mesh(name, verts, faces, mat)


def arch(name, radius=.42, spring=.9, thickness=.16, depth=.28, y=0):
    # Wedge faces lie in XZ, so their joints follow the arch rather than twisting in XY.
    for side in [-1, 1]:
        for row in range(3):
            box(name + '_jamb', (thickness, depth, spring / 3 - .015),
                (side * (radius + thickness / 2), y, (row + .5) * spring / 3), 'light')
    for i in range(9):
        a, b = i * math.pi / 9 + .012, (i + 1) * math.pi / 9 - .012
        pts = [(math.cos(t) * r, spring + math.sin(t) * r)
               for r, t in [(radius, a), (radius + thickness, a), (radius + thickness, b), (radius, b)]]
        polygon_prism(name + '_voussoir', pts, depth, y, 'light' if i % 3 else 'stone')


def window():
    arch('window', .16, .36, .075, .10)
    points = [(-.16, 0), (.16, 0)] + [(.16 * math.cos(i * math.pi / 8), .36 + .16 * math.sin(i * math.pi / 8)) for i in range(9)]
    polygon_prism('recessed_glass', points, .025, .028, 'glass')
    box('window_mullion', (.025, .035, .46), (0, -.04, .23), 'gold', .004)
    box('window_transom', (.30, .035, .025), (0, -.04, .27), 'gold', .004)
    box('projecting_sill', (.52, .21, .08), (0, -.025, .015), 'light')


def banner():
    points = [(-.20, .75), (.20, .75), (.20, .08), (.11, 0), (0, .09), (-.11, 0), (-.20, .08)]
    polygon_prism('banner_gold_hem', points, .025, 0, 'gold')
    polygon_prism('banner_blue_cloth', [(x * .82, z * .9 + .055) for x, z in points], .018, -.024, 'blue')
    crown = [(-.10, .30), (.10, .30), (.13, .49), (.055, .43), (0, .55), (-.055, .43), (-.13, .49)]
    polygon_prism('crown_emblem', crown, .02, -.04, 'gold')
    box('banner_crossbar', (.53, .055, .055), (0, 0, .79), 'gold')


def roof():
    # Individually pitched trapezoid tiles overlap at each course.
    rows = 5 if DETAIL else 3
    for side in range(4):
        angle = side * math.pi / 2
        for row in range(rows):
            t0, t1 = row / rows, (row + 1) / rows
            w0, w1 = .80 * (1 - t0), .80 * (1 - t1)
            count = max(1, rows - row)
            for j in range(count):
                a, b = -1 + 2 * j / count + .014, -1 + 2 * (j + 1) / count - .014
                verts = [(a*w0, -w0-.012, t0*1.12), (b*w0, -w0-.012, t0*1.12),
                         (b*w1, -w1-.012, t1*1.12+.015), (a*w1, -w1-.012, t1*1.12+.015)]
                verts = [(x*math.cos(angle)-y*math.sin(angle), x*math.sin(angle)+y*math.cos(angle), z) for x,y,z in verts]
                obj = mesh('blue_slate_course', verts, [(0,1,2,3)], ['blue','blue2','blue3'][(j+row+side)%3])
                solid = obj.modifiers.new('tile_thickness', 'SOLIDIFY')
                solid.thickness = .025
    cone('gold_finial', .10, .28, (0,0,1.24), 'gold', 4)


def capture(builder):
    before = set(bpy.context.scene.objects)
    builder()
    return list(set(bpy.context.scene.objects) - before)


def place(parts, name, pos=(0,0,0), scale=1, angle=0):
    result = []
    for src in parts:
        obj = src.copy()
        obj.data = src.data
        bpy.context.collection.objects.link(obj)
        x,y,z = src.location
        obj.location = (pos[0]+scale*(x*math.cos(angle)-y*math.sin(angle)),
                        pos[1]+scale*(x*math.sin(angle)+y*math.cos(angle)), pos[2]+scale*z)
        obj.scale = src.scale * scale
        obj.rotation_euler.z += angle
        obj.name = name + '__' + src.name
        result.append(obj)
    return result


def wall():
    box('wall_core', (2,.45,1.05), (0,0,.525), 'mortar')
    for row in range(4):
        for j in range(5):
            box('wall_ashlar', (.385,.48,.245), (-.8+j*.4,0,.13+row*.25), 'stone' if (row+j)%3 else 'light')
    box('wall_walk', (2.08,.61,.13), (0,0,1.07), 'light')
    for j in range(5):
        box('merlon', (.24,.44,.25), (-.88+j*.44,-.05,1.25), 'light')


def tower(kit):
    box('tower_foot', (1.30,1.30,.19), (0,0,.095), 'shade')
    box('tower_shaft', (1.03,1.03,1.65), (0,0,.99), 'stone')
    for z in [.30,.71,1.12,1.53]:
        for x,y in [(-.48,-.48),(.48,-.48),(-.48,.48),(.48,.48)]:
            box('corner_quoin', (.20,.20,.19), (x,y,z), 'light')
    for angle in [0,math.pi/2,math.pi,3*math.pi/2]:
        place(kit['window'], 'tower_window', (.535*math.sin(angle),-.535*math.cos(angle),.75), .8, angle)
    box('tower_cornice', (1.30,1.30,.15), (0,0,1.84), 'light')
    for x in [-.50,0,.50]:
        for y in [-.50,.50]:
            box('tower_battlement', (.24,.25,.23), (x,y,2.01), 'light')
    for x in [-.50,.50]:
        box('tower_side_merlon', (.25,.24,.23), (x,0,2.01), 'light')
    place(kit['roof'], 'tower_roof', (0,0,2.03), .71)


def gate(kit):
    arch('gate_arch', .48, .92, .21, .58)
    for side in [-1,1]:
        box('gate_buttress', (.28,.79,1.42), (side*.86,0,.71), 'stone')
        box('gate_pier_cap', (.40,.90,.14), (side*.86,0,1.45), 'light')
        place(kit['banner'], 'gate_royal_banner', (side*.85,-.425,.53), .68)
    box('gate_lintel', (1.54,.63,.22), (0,0,1.57), 'stone')
    for j in range(5):
        box('gate_crenel', (.24,.62,.22), (-.75+j*.375,0,1.79), 'light')
    for j in range(7):
        x = -.40+j*.133
        h = .91 + math.sqrt(max(0,.46**2-x*x))
        box('portcullis_oak', (.060,.08,h), (x,.19,h/2), 'wood', .009)
    for z in [.27,.65,1.0]:
        box('portcullis_iron', (.92,.07,.045), (0,.13,z), 'iron', .005)


def make_kit():
    kit = {}
    for name,builder in [('window',window),('banner',banner),('roof',roof),('wall',wall)]:
        kit[name] = capture(builder)
    kit['tower'] = capture(lambda: tower(kit))
    kit['gate'] = capture(lambda: gate(kit))
    # Detach templates from the scene; placements share their mesh data.
    for parts in kit.values():
        for obj in parts:
            for coll in list(obj.users_collection):
                coll.objects.unlink(obj)
    return kit


def ribbon(name, points, width, z, mat):
    verts=[]
    for i,(x,y) in enumerate(points):
        a=Vector(points[max(0,i-1)]); b=Vector(points[min(len(points)-1,i+1)])
        tangent=(b-a).normalized()
        for s in [-1,1]:
            verts.append((x-tangent.y*width*s/2,y+tangent.x*width*s/2,z))
    return mesh(name,verts,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)],mat)


def terrain():
    for radius,depth,z,mat in [(10,.64,-.50,'soil'),(10,.35,-.10,'earth'),(10,.12,.13,'grass')]:
        verts = [(radius*math.cos(math.pi/6+i*math.tau/6), radius*math.sin(math.pi/6+i*math.tau/6), z+dz)
                 for dz in [-depth/2,depth/2] for i in range(6)]
        faces = [tuple(reversed(range(6))),tuple(range(6,12))]
        faces += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
        mesh('hex_ground_'+mat,verts,faces,mat)
    verts=[(0,0,.21)]
    # Concentric hex rings create bounded, faceted grass without a circular overhang.
    count=60
    for ring in range(1,7):
        for i in range(count):
            edge,t=divmod(i,10)
            a=math.pi/6+edge*math.tau/6; b=a+math.tau/6
            x=(math.cos(a)*(1-t/10)+math.cos(b)*t/10)*9.98*ring/6
            y=(math.sin(a)*(1-t/10)+math.sin(b)*t/10)*9.98*ring/6
            verts.append((x,y,.205+RNG.uniform(0,.065) * (ring>2)))
    faces=[(0,1+i,1+(i+1)%count) for i in range(count)]
    for ring in range(1,6):
        a=1+(ring-1)*count; b=1+ring*count
        for i in range(count):
            j=(i+1)%count
            faces.extend([(a+i,b+i,b+j),(a+i,b+j,a+j)])
    obj=mesh('faceted_meadow',verts,faces,'grass')
    for mat in ['grass2','grass3']:
        obj.data.materials.append(M[mat])
    for poly in obj.data.polygons:
        poly.material_index=RNG.choices([0,1,2],[7,2,1])[0]
    points=[]
    for i in range(81):
        a=i*math.tau/80
        r=3.8+.16*math.sin(a*5)
        points.append((r*math.cos(a),r*.88*math.sin(a)))
    ribbon('moat_sandy_bank',points,.69,.29,'path')
    ribbon('turquoise_moat',points,.45,.305,'water')
    for start in [4,21,39,59,72]:
        ribbon('water_glint',points[start:start+5],.027,.317,'foam')
    ribbon('approach_road',[(0,-3),(0,-4.2),(.55,-5.1),(1.0,-6.3),(.6,-8.5)],.60,.29,'path')
    ribbon('village_lane',[(.4,-5.2),(2.7,-4.9),(5.0,-3),(6,-.3),(5.8,3)],.34,.295,'path')
    for i in range(8):
        box('bridge_paving',(.92,.23,.12),(0,-2.85-i*.23,.36),'light')
    for side in [-1,1]:
        box('bridge_low_parapet',(.10,1.9,.21),(side*.48,-3.65,.47),'stone')


def tree(x,y,s):
    box('pine_trunk',(.16*s,.16*s,.60*s),(x,y,.3+.3*s),'wood')
    for i in range(3):
        cone('pine_canopy',(.55-i*.11)*s,.93*s,(x,y,.75*s+i*.35*s+.3),'pine' if i%2==0 else 'pine2',7)


def landscape(kit):
    for x,y,s in [(-7,-3,1),(-6,-4.2,.8),(-7.1,1.3,1.1),(-6,3.6,.9),(-4.8,5.8,.85),(-2.3,7,.9),(1.5,6.8,1),(5,5.3,.85),(7,1.3,.9),(6.7,-2.8,.8),(3,-6.8,.6),(-4,-6.6,.6)]:
        tree(x,y,s)
    for x,y in [(-6,-1),(-4.9,4.3),(5.3,2.8),(3.9,-6),(-3.5,-7.2)]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=.44,location=(x,y,.46))
        bpy.context.object.scale=(1.2,.8,.7)
        bpy.context.object.name='meadow_boulder'
        bpy.context.object.data.materials.append(M['shade'])
    for x,y in [(3.8,-3.9),(5.0,-2.4),(-4.9,-2.6)]:
        box('village_cottage',(.86,.73,.65),(x,y,.61),'light')
        place(kit['roof'],'cottage_roof',(x,y,.95),.66)
        box('cottage_door',(.18,.025,.37),(x,y-.38,.49),'wood')
    for x,y in [(3.2,-5.7),(4.3,-4.9)]:
        box('crop_soil',(.86,.93,.045),(x,y,.3),'soil')
        for i in range(6):
            box('golden_crop_row',(.09,.85,.14),(x-.34+i*.135,y,.40),'wheat',.01)
    for i in range(110 if DETAIL else 30):
        x,y=RNG.uniform(-7.3,7.3),RNG.uniform(-7.3,7.3)
        if math.hypot(x,y)<4.5 or abs(x)+abs(y)>10.5:
            continue
        cone('meadow_tuft',.08,.18,(x,y,.34),'grass3',5)
        if i%4==0:
            cone('wildflower',.055,.055,(x+.05,y,.43),'flower',6)


def create_city_block(detailed=True):
    global DETAIL
    DETAIL=detailed
    RNG.seed(918)
    palette()
    kit=make_kit()
    terrain()
    box('castle_foundation',(6.2,5.35,.16),(0,.12,.35),'shade')
    # Four perimeter towers, split front walls and a real central gate opening.
    for x in [-2.45,2.45]:
        for y in [-1.98,2.22]:
            place(kit['tower'],'perimeter_tower',(x,y,.43))
    for x in [-1.65,1.65]:
        place(kit['wall'],'front_wall',(x,-1.98,.43),.70)
    for x in [-1.25,.75]:
        place(kit['wall'],'rear_wall',(x,2.22,.43))
    for x in [-2.45,2.45]:
        for y in [-.93,1.07]:
            place(kit['wall'],'side_wall',(x,y,.43),1,math.pi/2)
    place(kit['gate'],'entry_gate',(0,-1.99,.43))
    box('great_hall',(2.10,1.65,1.28),(0,.58,1.07),'light')
    place(kit['roof'],'hall_roof',(0,.58,1.71),1.45)
    place(kit['tower'],'royal_keep',(0,1.03,1.82),1.13)
    place(kit['banner'],'keep_standard',(0,.43,2.98),.85)
    box('royal_flagpole',(.035,.035,.66),(0,1.03,5.20),'gold')
    polygon_prism('royal_flag',[(.02,5.48),(.53,5.41),(.43,5.28),(.02,5.31)],.025,1.03,'blue2')
    for x in [-.63,.63]:
        place(kit['window'],'hall_window',(x,-.26,.90))
    for y in [-1.5,-1.05,-.60]:
        for x in [-.36,0,.36]:
            box('courtyard_paver',(.34,.40,.04),(x,y,.46),'light',.015)
    landscape(kit)
    # Match existing tile asset convention: roughly two units wide, Z-up.
    for obj in list(bpy.context.scene.objects):
        obj.location *= .1
        obj.scale *= .1
    return kit


def setup_camera(target, location, ortho, output):
    scene=bpy.context.scene
    bpy.ops.object.camera_add(location=location)
    cam=bpy.context.object
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO'; cam.data.ortho_scale=ortho
    scene.camera=cam
    scene.render.engine='CYCLES'
    scene.cycles.samples=32
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1600; scene.render.resolution_y=1400
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(output)
    scene.world.color=(.16,.16,.16)
    scene.view_settings.view_transform='AgX'
    for pos,energy,size in [((-2,-3,5),450,3),((3,2,4),300,2)]:
        bpy.ops.object.light_add(type='AREA',location=pos)
        lamp=bpy.context.object; lamp.data.energy=energy; lamp.data.shape='DISK'; lamp.data.size=size
        lamp.rotation_euler=(Vector((0,0,0))-lamp.location).to_track_quat('-Z','Y').to_euler()
    return cam


def export(path, objects):
    path.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True)


def main():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.context.preferences.filepaths.save_version=0
    kit=create_city_block()
    assets=ROOT/'src/render/assets'
    previews=ROOT/'artifacts'
    previews.mkdir(exist_ok=True)
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    export(assets/'buildables/buildable-city-center-lod0.glb',objects)
    cam=setup_camera((0,0,.05),(2.7,-4,3.2),2.55,previews/'capital-v2-tile.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/buildables/buildable-city-center.blend'))
    bpy.ops.render.render(write_still=True)
    cam.location=(1.3,-2.2,1.45)
    cam.rotation_euler=(Vector((0,0,.23))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=1.13
    bpy.context.scene.render.filepath=str(previews/'capital-v2-closeup.png')
    bpy.ops.render.render(write_still=True)
    for obj in objects:
        bpy.data.objects.remove(obj,do_unlink=True)
    for index,(name,parts) in enumerate(kit.items()):
        placed=place(parts,'module_'+name,scale=.1)
        export(assets/('buildables/modules/capital-v2-'+name+'.glb'),placed)
        for obj in placed:
            obj.location.x+=(index%3-1)*.48
            obj.location.y+=(1-index//3)*.50-.25
    cam.location=(1,-2,1.8)
    cam.rotation_euler=(Vector((0,0,.10))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=1.75
    bpy.context.scene.render.filepath=str(previews/'capital-v2-kit.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(assets/'source/buildables/modules/capital-v2-kit.blend'))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    create_city_block(False)
    export(assets/'buildables/buildable-city-center-lod1.glb',[o for o in bpy.context.scene.objects if o.type=='MESH'])


if __name__=='__main__':
    main()
