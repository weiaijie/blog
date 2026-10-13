"""Reference-led C-style map elements, in meters, Z-up with front at -Y.

Run with Blender 4.5: blender -b --factory-startup --python-exit-code 1
  --python scripts/blender/map_element_kit.py
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import map_element_botany
import map_element_fauna
import map_element_buildings
import map_element_fortifications
import map_element_crops
import map_element_trees
import map_element_understory
import map_element_meadow
import map_element_conifer_reed
import map_element_landforms
import map_element_people
import map_element_routes
import map_element_transport
import map_element_mounted
import map_element_steam
import map_element_vessels
import map_element_workshops
import map_element_industry
import map_element_bridges
import map_element_hydraulics
import map_element_civic
import map_element_riparian

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/render/assets/elements'
SOURCE = ROOT / 'src/render/assets/source/elements'
M = {}
RNG = random.Random(20261012)


def palette():
    colors = {
        'wood': '87714F', 'wood_light': 'A58C66', 'wood_dark': '63513D',
        'iron': '515A5C', 'rope': 'BAA278', 'teal': '538E92',
        'leaf': '659341', 'leaf_light': '94B653', 'leaf_dark': '39633C',
        'gold': 'CFAB51', 'grain': 'E5C66C', 'earth': '746047',
        'earth_light': '957951', 'berry': 'AC4251', 'bark': '66513E',
        'stone': '939589', 'stone_light': 'B2B3A4', 'tile': 'BE6846',
        'wool': 'E3D9BD', 'wool_light': 'EEE6CD', 'skin': '68685D',
        'hoof': '444943', 'eye': '191F20', 'fish': '7FABA3',
        'fish_dark': '4F7A76', 'belly': 'D5D9C8', 'fin': 'BFAC6F',
        'pine': '356542', 'pine_light': '598448', 'pine_dark': '264D36',
        'loam_dark': '594332', 'loam': '725438', 'loam_light': '806044',
        'loam_dry': '8E6D4B', 'straw': 'B69543', 'straw_light': 'D3B45A',
        'straw_green': '8B8D42', 'ripe_grain': 'D9B867',
        'field_blend': 'FFFFFF', 'cabbage_outer': '638B50',
        'cabbage_middle': '82A963', 'cabbage_inner': 'A0BB77',
        'edge_grass': '7B9250',
    }
    M.clear()
    for name, code in colors.items():
        rgb = [int(code[i:i+2], 16) / 255 for i in (0, 2, 4)]
        linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb]
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*linear, 1)
        mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*linear, 1)
        shader.inputs['Roughness'].default_value = .85
        shader.inputs['Metallic'].default_value = .25 if name == 'iron' else 0
        M[name] = mat


def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    data.materials.append(M[mat])
    return obj


def box(name, pos, size, mat='wood', bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(M[mat])
    if bevel:
        mod = obj.modifiers.new('cut_edges', 'BEVEL')
        mod.width = min(bevel, min(size) * .2)
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj


def ico(name, pos, size, mat, detail=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detail, radius=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(M[mat])
    return obj


def beam(name, a, b, width, mat='wood', sides=6, end=None):
    delta = Vector(b) - Vector(a)
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=width,
                                   radius2=width if end is None else end,
                                   depth=delta.length, location=(Vector(a) + Vector(b)) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    obj.data.materials.append(M[mat])
    return obj


def pivot(name, pos, objects):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.location = pos
    bpy.context.view_layer.update()
    for child in objects:
        world = child.matrix_world.copy()
        child.parent = obj
        child.matrix_world = world
    return obj


def capture(builder):
    before = set(bpy.context.scene.objects)
    builder()
    return list(set(bpy.context.scene.objects) - before)


def sway(obj, axis, amount, phase=0, spin=False):
    base = obj.rotation_euler[axis]
    for frame in range(1, 74, 3):
        t = (frame - 1) / 72
        obj.rotation_euler[axis] = base + (t * math.tau if spin else math.sin(t * math.tau + phase) * amount)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame)
    obj.rotation_euler[axis] = base


def blade(name, x, y, height, angle, mat='leaf', width=.055):
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy * width, dx * width
    return mesh(name, [(x-nx, y-ny, 0), (x+nx, y+ny, 0),
                       (x+dx*.16+nx*.5, y+dy*.16+ny*.5, height*.6),
                       (x+dx*.35, y+dy*.35, height),
                       (x+dx*.16-nx*.5, y+dy*.16-ny*.5, height*.6)],
                [(0, 1, 2), (0, 2, 4), (4, 2, 3)], mat)


def soil():
    box('thin_soil_surface', (0, 0, .018), (2.8, 2.8, .036), 'earth', 0)


def plowed():
    soil()
    for row in range(6):
        x = -.115e1 + row * .46
        verts = []
        for j in range(15):
            y = -1.38 + j * 2.76 / 14
            for offset, z in [(-.19, .035), (-.08, .13), (.035, .17), (.18, .04)]:
                verts.append((x+offset+RNG.uniform(-.025, .025), y, z+RNG.uniform(-.015, .015)))
        faces = []
        for j in range(14):
            for k in range(3):
                a = j*4+k
                faces.extend([(a, a+4, a+5), (a, a+5, a+1)])
        ridge = mesh('furrow', verts, faces, 'earth_light')
        ridge.data.materials.append(M['earth'])
        for face in ridge.data.polygons:
            face.material_index = RNG.randrange(2)
    for _ in range(32):
        ico('clod', (RNG.uniform(-1.3, 1.3), RNG.uniform(-1.3, 1.3), .08), (.04, .06, .04), 'earth')


def field_height(x, y):
    # Broad rounded crowns and shared low borders, not disconnected triangular strips.
    phase = (x + 1.15 + .015 * math.sin(y * 4)) / .46
    crown = (.5 + .5 * math.cos(phase * math.tau)) ** 1.3
    margin = max(0, min(1, (1.4-abs(x))/.12, (1.4-abs(y))/.22))
    margin = margin * margin * (3-2*margin)
    return .045 + margin * (.105*crown + .009*math.sin(x*29+y*7)*math.sin(y*21))


def field_surface(columns=48, rows=40, clods=110):
    vertices = []
    for j in range(rows+1):
        for i in range(columns+1):
            x, y = -1.4+i*2.8/columns, -1.4+j*2.8/rows
            if 0<i<columns and 0<j<rows:
                x += RNG.uniform(-.014,.014)
                y += RNG.uniform(-.018,.018)
            vertices.append((x,y,field_height(x,y)))
    faces = []
    for j in range(rows):
        for i in range(columns):
            a=j*(columns+1)+i; b=a+1; c=a+columns+1; d=c+1
            faces.extend([(a,b,c),(b,d,c)] if (i+j)%2 else [(a,b,d),(a,d,c)])
    surface_count = len(faces)
    boundary = (list(range(columns+1)) +
                [j*(columns+1)+columns for j in range(1,rows+1)] +
                [rows*(columns+1)+i for i in range(columns-1,-1,-1)] +
                [j*(columns+1) for j in range(rows-1,0,-1)])
    bottom = len(vertices)
    vertices.extend([(vertices[i][0],vertices[i][1],0) for i in boundary])
    for i,a in enumerate(boundary):
        n=(i+1)%len(boundary)
        faces.append((a,bottom+i,bottom+n,boundary[n]))
    faces.append(tuple(reversed(range(bottom,len(vertices)))))
    earth = mesh('continuous_tilled_soil',vertices,faces,'loam_dark')
    for name in ['loam','loam_light','loam_dry']:
        earth.data.materials.append(M[name])
    for face in earth.data.polygons:
        if face.index >= surface_count:
            continue
        z=sum(earth.data.vertices[v].co.z for v in face.vertices)/len(face.vertices)
        face.material_index = 0 if z<.065 else 1 if z<.105 else 2 if z<.137 else 3
    for _ in range(clods):
        x,y=RNG.uniform(-1.34,1.34),RNG.uniform(-1.34,1.34)
        radius=RNG.uniform(.018,.041)
        obj=ico('embedded_soil_clod',(x,y,field_height(x,y)-radius*.15),
                (radius*1.3,radius,radius*.65),'loam_light' if RNG.random()<.6 else 'loam',1)
        obj.rotation_euler.z=RNG.uniform(0,math.tau)
        for v in obj.data.vertices:
            v.co *= RNG.uniform(.8,1.12)


def plowed_refined():
    field_surface()


def wheat_refined(natural=False):
    if natural:
        living_soil()
    else:
        field_surface(36,24,28)
    for row in range(6):
        for j in range(21):
            if natural and RNG.random() < .085:
                continue
            before=set(bpy.context.scene.objects)
            x=-1.15+row*.46+RNG.uniform(-.085,.085)
            y=-1.25+j*.125+RNG.uniform(-.026,.026)
            if natural:
                x += .055*math.sin(y*2.6+row*.4)
                y += RNG.uniform(-.033,.033)
            ground=living_height(x,y) if natural else field_height(x,y)
            h=RNG.uniform(.52,.81) if natural else RNG.uniform(.64,.9)
            angle=RNG.uniform(0,math.tau)
            lean=Vector((math.cos(angle),math.sin(angle),0))*RNG.uniform(.07,.15)
            root=Vector((x,y,ground))
            centers=[root+lean*t*t+Vector((0,0,h*t)) for t in [0,.4,.75,1]]
            verts=[]
            for n,p in enumerate(centers):
                for k in range(3):
                    a=k*math.tau/3
                    verts.append(tuple(p+Vector((math.cos(a),math.sin(a),0))*(.008-n*.001)))
            faces=[]
            for n in range(3):
                for k in range(3):
                    a=n*3+k; b=n*3+(k+1)%3
                    faces.append((a,b,b+3,a+3))
            faces.extend([(2,1,0),(9,10,11)])
            stem_material='straw_green' if RNG.random()<.16 else 'straw'
            mesh('curved_wheat_stem',verts,faces,stem_material)
            leaf_levels=[(.2,0),(.38,2.65),(.59,4.8)] if natural else [(.28,0),(.52,2.65)]
            for level,turn in leaf_levels:
                a=angle+turn
                direction=Vector((math.cos(a),math.sin(a),0))
                across=Vector((-direction.y,direction.x,0))
                start=root+lean*level*level+Vector((0,0,h*level))
                verts=[]
                for n,(distance,lift,width) in enumerate([(0,0,.006),(.08,.17,.036),(.24,.2,.027),(.4,.11,0)]):
                    center=start+direction*distance+Vector((0,0,lift))
                    verts.extend([tuple(center-across*width),tuple(center+Vector((0,0,.012 if n in [1,2] else 0))),tuple(center+across*width)])
                faces=[]
                for n in range(3):
                    a=n*3
                    faces.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
                mesh('arched_wheat_leaf',verts,faces,stem_material)
            head=centers[-1]
            head_before=set(bpy.context.scene.objects)
            axis=Vector((lean.x*1.8,lean.y*1.8,1)).normalized()
            width=Vector((-math.sin(angle),math.cos(angle),0))
            depth=axis.cross(width).normalized()
            for tier in range(5 if natural else 4):
                for side in [-1,1]:
                    p=head+axis*(tier*.037)+width*(side*.017)
                    # Tapered six-face kernels overlap around the rachis, not floating beads.
                    verts=[tuple(p-width*.018-depth*.014),tuple(p+width*.018-depth*.014),
                           tuple(p+width*.018+depth*.014),tuple(p-width*.018+depth*.014),
                           tuple(p+axis*.051+width*side*.018)]
                    mesh('overlapping_wheat_kernel',verts,[(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],
                         'ripe_grain' if tier%2 else 'straw_light')
            for side in [-1,0,1]:
                p=head+axis*.135+width*side*.012
                mesh('short_awn',[tuple(p-width*.002),tuple(p+width*.002),tuple(p+axis*.09+width*side*.014)],[(0,1,2)],'straw_light')
            if natural:
                head_node=pivot('WheatHead',head,list(set(bpy.context.scene.objects)-head_before))
                head_node['cropPart']='head'
                parts=list(set(bpy.context.scene.objects)-before)
                root_parts=[obj for obj in parts if obj.parent is None]
                plant=pivot('WheatPlant',root,root_parts)
                plant['crop']='wheat'
                plant['vigor']=RNG.uniform(.82,1.12)


def soil_weight(x,y):
    radius=((abs(x)/1.38)**6+(abs(y)/1.38)**6)**(1/6)
    irregular=.045*math.sin(x*9+y*3)+.035*math.sin(y*11-x*2)
    t=max(0,min(1,(1.12-radius+irregular)/.26))
    return t*t*(3-2*t)


def living_height(x,y):
    # Shared flat outside border; cultivation dies away before the grassy perimeter.
    edge=max(0,min(1,(1.75-max(abs(x),abs(y)))/.18))
    phase=(x+.055*math.sin(y*2.6)+1.15)/.46
    crown=(.5+.5*math.cos(phase*math.tau))**1.2
    return .055+edge*(soil_weight(x,y)*(.082*crown+.008*math.sin(x*29+y*5)*math.cos(y*27))
                       +.008*math.sin(x*8+y*5)*math.cos(y*6))


def living_soil(height=living_height, weight=soil_weight):
    columns,rows=48,40
    verts=[]
    for j in range(rows+1):
        for i in range(columns+1):
            x,y=-1.75+i*3.5/columns,-1.75+j*3.5/rows
            if 0<i<columns and 0<j<rows:
                x+=RNG.uniform(-.02,.02);y+=RNG.uniform(-.02,.02)
            verts.append((x,y,height(x,y)))
    faces=[]
    for j in range(rows):
        for i in range(columns):
            a=j*(columns+1)+i;b=a+1;c=a+columns+1;d=c+1
            faces.extend([(a,b,d),(a,d,c)] if RNG.random()<.5 else [(a,b,c),(b,d,c)])
    top_faces=len(faces)
    boundary=(list(range(columns+1))+[j*(columns+1)+columns for j in range(1,rows+1)]
              +[rows*(columns+1)+i for i in range(columns-1,-1,-1)]
              +[j*(columns+1) for j in range(rows-1,0,-1)])
    bottom=len(verts)
    verts.extend([(verts[i][0],verts[i][1],0) for i in boundary])
    for i,a in enumerate(boundary):
        n=(i+1)%len(boundary)
        faces.append((a,bottom+i,bottom+n,boundary[n]))
    faces.append(tuple(reversed(range(bottom,len(verts)))))
    obj=mesh('soil_grass_transition',verts,faces,'field_blend')
    obj['fieldSurface']=True
    colors=obj.data.color_attributes.new(name='SoilBlend',type='FLOAT_COLOR',domain='CORNER')
    material=M['field_blend']
    color_node=material.node_tree.nodes.new('ShaderNodeVertexColor')
    color_node.layer_name='SoilBlend'
    material.node_tree.links.new(color_node.outputs['Color'],material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
    for face in obj.data.polygons:
        for loop in face.loop_indices:
            x,y,z=obj.data.vertices[obj.data.loops[loop].vertex_index].co
            w=weight(x,y)
            crest=max(0,min(1,(z-.055)/.1))
            earth=(.32+.15*crest,.235+.115*crest,.145+.075*crest)
            grass=(.33,.42,.205)
            shade=.96+.045*math.sin(x*15+y*13)
            rgb=[((grass[c]*(1-w)+earth[c]*w)*shade) if face.index<top_faces else (.29,.24,.16)[c] for c in range(3)]
            linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
            colors.data[loop].color=(*linear,1)
    for _ in range(95):
        x,y=RNG.uniform(-1.6,1.6),RNG.uniform(-1.6,1.6)
        radius=RNG.uniform(.012,.035)
        ico('embedded_crumb',(x,y,height(x,y)-radius*.16),
            (radius*1.4,radius,radius*.6),'loam' if weight(x,y)>.5 else 'earth',1)
    for i in range(32):
        angle=RNG.uniform(0,math.tau)
        radius=RNG.uniform(1.4,1.63)
        x,y=radius*math.cos(angle),radius*math.sin(angle)
        if weight(x,y)>.8:
            continue
        ground=height(x,y)
        parts=[]
        for j in range(5):
            leaf=blade('margin_grass',x,y,RNG.uniform(.07,.16),angle+j*2.3,'edge_grass',.035)
            for vertex in leaf.data.vertices:
                vertex.co.x=x+(vertex.co.x-x)*.45
                vertex.co.y=y+(vertex.co.y-y)*.45
            leaf.location.z=ground
            parts.append(leaf)
        root=pivot('MarginGrass',(x,y,ground),parts)
        root['crop']='edge-grass'


def cabbage_leaf(center,angle,radius,height,width,mat):
    direction=Vector((math.cos(angle),math.sin(angle),0))
    across=Vector((-direction.y,direction.x,0))
    verts=[]
    for i in range(5):
        t=i/4
        distance=radius*math.sin(t*math.pi*.82)
        lift=height*math.sin(t*math.pi*.58)
        for j in [-1,0,1]:
            span=width*math.sin(t*math.pi)*j
            edge=.025*(j*j)*math.sin(t*math.pi)
            p=Vector(center)+direction*distance+across*span+Vector((0,0,lift+edge))
            verts.append(tuple(p))
    faces=[]
    for i in range(4):
        a=i*3
        faces.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
    return mesh('curled_cabbage_leaf',verts,faces,mat)


def vegetables_living():
    living_soil()
    for row in range(5):
        for col in range(4):
            if (row,col) in [(0,2),(3,0)]:
                continue
            x=-.97+col*.63+RNG.uniform(-.075,.075)+.06*math.sin(row*1.7)
            y=-1.03+row*.5+RNG.uniform(-.075,.075)
            z=living_height(x,y)
            angle=RNG.uniform(0,math.tau)
            size=RNG.uniform(.78,1.12)
            leaves=[];inner=[]
            for layer,(count,r,h,w,material) in enumerate([
                (8,.32,.085,.105,'cabbage_outer'),(7,.23,.19,.105,'cabbage_middle'),
                (6,.145,.29,.095,'cabbage_inner')]):
                for i in range(count):
                    leaf=cabbage_leaf((x,y,z+.012+layer*.01),angle+i*2.399+layer*.6,
                                      r*size*RNG.uniform(.92,1.1),h*size,w*size,material)
                    (inner if layer==2 else leaves).append(leaf)
            head=pivot('CabbageHeart',(x,y,z+.03),inner)
            head['cropPart']='head'
            root=pivot('CabbagePlant',(x,y,z),leaves+[head])
            root['crop']='cabbage'
            root['vigor']=RNG.uniform(.8,1.13)


def wheat():
    soil()
    for row in range(6):
        for j in range(18):
            x, y = -1.15 + row*.46 + RNG.uniform(-.085, .085), -1.23+j*.145
            h = RNG.uniform(.49, .68)
            beam('wheat_stem', (x, y, .025), (x, y, h), .009, 'gold', 4)
            for n in range(4):
                z = h - .10 + n*.047
                for s in [-1, 1]:
                    gx = x+s*.028
                    mesh('grain', [(gx-.021,y,z),(gx+.021,y,z),(gx,y-.025,z),(gx,y+.025,z),
                                   (gx+s*.015,y,z+.047),(gx-s*.015,y,z-.032)],
                         [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)],'grain')
            beam('awn', (x, y, h+.07), (x+.035, y, h+.19), .005, 'grain', 3)
            for n in range(2):
                leaf = blade('wheat_leaf', x, y, h*.71, row+n*2.8, 'gold', .035)
                leaf.location.z = .025


def vegetables():
    soil()
    for row in range(4):
        for col in range(4):
            x, y = -.99 + col*.66, -.99 + row*.66
            ico('cabbage_heart', (x, y, .19), (.18, .18, .2), 'leaf_light', 2)
            for n in range(6):
                a = n*math.tau/6
                dx, dy = math.cos(a), math.sin(a)
                nx, ny = -dy, dx
                verts = [(x, y, .08), (x+dx*.24+nx*.14, y+dy*.24+ny*.14, .09),
                         (x+dx*.31, y+dy*.31, .25), (x+dx*.24-nx*.14, y+dy*.24-ny*.14, .09),
                         (x+dx*.15, y+dy*.15, .22)]
                mesh('cupped_cabbage_leaf', verts, [(0,1,4),(1,2,4),(2,3,4),(3,0,4)], 'leaf')


def bridge():
    for side in [-1, 1]:
        x = side*1.05
        box('longitudinal_stringer', (x, 0, 1.0), (.18, 5.8, .25))
        for y in [-2.65, -.9, .9, 2.65]:
            box('railing_post', (x, y, 1.65), (.2, .2, 1.3), 'wood_light', .035)
            box('post_iron', (x, y, 1.18), (.225, .225, .14), 'iron')
            ico('bolt', (x+side*.12, y, 1.18), (.028, .036, .036), 'iron')
        for z in [1.55, 2.05]:
            box('guardrail', (x, 0, z), (.105, 5.5, .105), 'wood_light')
        for y in [-1.9, 1.9]:
            box('pile', (x, y, .55), (.25, .25, 1.1))
    for j in range(29):
        box('deck_plank', (0, -2.8+j*.2, 1.16), (2.3, .19, .13), 'wood_light' if j%3 else 'wood')
    for y in [-1.9, 1.9]:
        for side in [-1,1]:
            beam('trestle_crossbrace', (-1, y+side*.035, .16 if side==1 else .98),
                 (1, y+side*.035, .98 if side==1 else .16), .085, 'wood_dark', 4)


def fishing_boat():
    # Nested cross-sections form a real open shell, not an ellipsoid with a lid.
    stations = [(-2.35,.025,.62),(-1.95,.43,.26),(-1.25,.72,.08),(-.35,.85,0),(.65,.82,.03),(1.55,.68,.15),(2.1,.55,.32)]
    rings = []
    for y,w,b in stations:
        rings.append([(-w,y,.86),(-w*.79,y,b+.22),(-w*.38,y,b+.025),(0,y,b),
                      (w*.38,y,b+.025),(w*.79,y,b+.22),(w,y,.86)])
    outer = [point for ring in rings for point in ring]
    inner = [(x*.91,y,z+.065) for x,y,z in outer]
    count = len(outer)
    faces = []
    for j in range(len(rings)-1):
        for k in range(6):
            a=j*7+k
            faces.extend([(a,a+7,a+8,a+1),(a+count+1,a+count+8,a+count+7,a+count)])
        for k in [0,6]:
            a=j*7+k
            faces.append((a,a+count,a+count+7,a+7))
    for j in [0,len(rings)-1]:
        for k in range(6):
            a=j*7+k
            faces.append((a,a+1,a+1+count,a+count))
    hull=mesh('closed_hull_shell',outer+inner,faces,'wood')
    hull.data.materials.append(M['wood_light']);hull.data.materials.append(M['wood_dark'])
    for face in hull.data.polygons:
        face.material_index=1 if face.index%6==0 else 0
    for side in [-1,1]:
        for j in range(len(stations)-1):
            y,w,_ = stations[j]; yy,ww,_ = stations[j+1]
            beam('teal_gunwale', (side*w,y,.88), (side*ww,yy,.88), .045, 'teal', 5)
        for ring in rings[1:-1]:
            points=[(x*.88,y,z+.09) for x,y,z in ring]
            for k in (range(3) if side<0 else range(3,6)):
                beam('interior_rib',points[k],points[k+1],.024,'wood_light',4)
    box('transom', (0,2.1,.64), (1.1,.085,.49), 'wood')
    for y,w in [(-1.25,1.25),(-.05,1.55),(1.1,1.35)]:
        box('thwart', (0,y,.71), (w,.23,.08), 'wood_light')
    for i in range(5):
        box('floorboard', ((i-2)*.13,.2,.23), (.12,1.95,.045), 'wood')
    beam('bow_stem', (0,-2.36,.4), (0,-2.36,1.04), .055, 'wood_light', 5)
    for side in [-1,1]:
        def oar():
            beam('oar_shaft', (side*.55,-.25,.97), (side*1.82,-.25,.72), .025, 'wood_light')
            paddle = box('oar_blade', (side*1.96,-.25,.68), (.46,.16,.04), 'wood_light')
            paddle.rotation_euler.y = side*.17
        group = pivot('Oar_L' if side<0 else 'Oar_R', (side*.78,-.25,.92), capture(oar))
        sway(group, 2, .22, side*.7)
    for i in range(4):
        r = .09+i*.028
        for j in range(16):
            a,b = j*math.tau/16,(j+1)*math.tau/16
            beam('rope_coil', (.28+r*math.cos(a),1.65+r*math.sin(a),.64),
                 (.28+r*math.cos(b),1.65+r*math.sin(b),.64), .013, 'rope', 4)


def pine():
    beam('trunk', (0,0,0), (0,0,3.7), .16, 'bark', 7, .045)
    for j in range(5):
        z,r = .8+j*.59,1.08-j*.18
        verts = [(0,0,z+1.18-j*.05)]
        for level in [0,1]:
            for i in range(24):
                a=i*math.tau/24+j*.37
                rr = r * (1 if level==0 else .55) * (1 if i%2==0 else .73) * RNG.uniform(.90,1.10)
                verts.append((math.cos(a)*rr,math.sin(a)*rr,z+(i%2)*.23+level*.51))
        faces=[]
        for i in range(24):
            n=(i+1)%24
            faces.extend([(1+i,1+n,25+i),(1+n,25+n,25+i),(25+i,25+n,0)])
        faces.append(tuple(reversed(range(1,25))))
        obj=mesh('angular_bough_tier',verts,faces,'pine_dark' if j<2 else 'pine')
        obj.data.materials.append(M['pine_light'])
        for f in obj.data.polygons:
            f.material_index=1 if RNG.random()<.18 else 0
    for a in [0,2.4,4.6]:
        beam('low_branch',(0,0,.65),(.3*math.cos(a),.3*math.sin(a),1.0),.045,'bark')


def shrub():
    for x,y,z,s in [(-.36,0,.5,.45),(.34,.08,.56,.4),(0,.05,.91,.5),(.04,-.2,.43,.35)]:
        beam('branch',(0,0,0),(x,y,z),.035,'bark',5)
        crown=ico('faceted_foliage',(x,y,z),(s,s*.73,s),'leaf',2)
        for v in crown.data.vertices:
            v.co *= RNG.uniform(.84,1.14)
        crown.data.materials.append(M['leaf_dark']);crown.data.materials.append(M['leaf_light'])
        for face in crown.data.polygons:
            face.material_index=RNG.choices([0,1,2],[6,2,2])[0]
    for x,y,z in [(-.54,-.22,.52),(-.18,-.37,.62),(.24,-.23,.72),(.03,-.3,1.06),(.5,-.15,.45),(-.29,-.21,.96),(.15,-.29,.35)]:
        ico('berry',(x,y,z),(.063,.063,.065),'berry')


def reeds():
    for i,(x,y,h) in enumerate([(-.19,-.06,1.25),(.08,.05,1.63),(.22,-.13,1.32),(-.05,-.2,.97),(.24,.17,1.07)]):
        parts=[]
        parts.append(beam('reed_stem',(x,y,0),(x,y,h),.014,'leaf',5))
        parts.append(ico('cattail',(x,y,h),(.05,.05,.18),'wood',2))
        for n in range(2):
            parts.append(blade('reed_leaf',x,y,h*.65,i*1.7+n*2.5,'leaf',.033))
        group=pivot('Reed_'+str(i),(x,y,0),parts)
        sway(group,1,.035,i*.8)


def fish():
    rings=[(-.73,.01,.04),(-.6,.14,.18),(-.32,.21,.31),(.05,.22,.32),(.39,.13,.22),(.66,.038,.07)]
    verts=[]
    for y,w,h in rings:
        for i in range(10):
            a=i*math.tau/10
            verts.append((math.sin(a)*w,y,.36+math.cos(a)*h))
    faces=[]
    for j in range(len(rings)-1):
        for i in range(10):
            a=j*10+i;b=j*10+(i+1)%10
            faces.extend([(a,b,b+10),(a,b+10,a+10)])
    faces.extend([tuple(reversed(range(10))),tuple(range(50,60))])
    obj=mesh('streamlined_body',verts,faces,'fish')
    obj.data.materials.append(M['belly']);obj.data.materials.append(M['fish_dark'])
    for f in obj.data.polygons:
        z=sum(obj.data.vertices[v].co.z for v in f.vertices)/len(f.vertices)
        f.material_index=1 if z<.24 else 2 if z>.51 else 0
    for side in [-1,1]:
        ico('gold_eye_rim',(side*.105,-.58,.42),(.033,.046,.046),'fin',2)
        ico('eye',(side*.127,-.594,.426),(.021,.025,.025),'eye',2)
        mesh('pectoral_fin',[(side*.16,-.3,.26),(side*.35,-.05,.16),(side*.19,.02,.26)],[(0,1,2)],'fin')
    mesh('dorsal_fin',[(0,-.22,.62),(0,.02,.85),(0,.26,.59)],[(0,1,2)],'fin')
    tail=mesh('forked_tail',[(0,.64,.36),(0,1.05,.74),(0,.94,.37),(0,1.05,-.01)],[(0,1,2),(0,2,3)],'fin')
    group=pivot('Tail',(0,.62,.36),[tail]);sway(group,2,.4)


def sheep():
    body=ico('wool_body',(0,.08,.86),(.44,.69,.45),'wool',3)
    for v in body.data.vertices:
        v.co *= RNG.uniform(.95,1.055)
    for x in [-.25,.25]:
        for y in [-.36,.47]:
            beam('upper_leg',(x,y,.77),(x,y+.04,.31),.081,'skin',6,.059)
            beam('lower_leg',(x,y+.04,.36),(x,y-.01,.08),.052,'skin',6,.044)
            box('cloven_hoof',(x,y-.035,.055),(.11,.17,.11),'hoof',.018)
    parts=capture(lambda: sheep_head())
    head=pivot('Head',(0,-.44,1.05),parts);sway(head,0,.09)
    tail=ico('short_tail',(0,.75,.9),(.09,.17,.09),'wool')
    group=pivot('Tail',(0,.64,.94),[tail]);sway(group,1,.12)


def sheep_head():
    ico('neck_fleece',(0,-.48,1.16),(.3,.3,.35),'wool',2)
    ico('tapered_face',(0,-.77,1.13),(.19,.27,.29),'skin',2)
    ico('muzzle',(0,-.93,.98),(.14,.11,.11),'hoof',1)
    ico('forehead_fleece',(0,-.66,1.39),(.2,.21,.12),'wool_light',2)
    for side in [-1,1]:
        ear=ico('ear',(side*.28,-.7,1.3),(.19,.065,.08),'skin',1)
        ear.rotation_euler.y=side*.3
        ico('eye',(side*.152,-.88,1.24),(.034,.026,.037),'eye',2)


def well():
    for row in range(3):
        for j in range(12):
            a=(j+row*.5)*math.tau/12; b=a+math.tau/12-.025
            verts=[(math.cos(t)*r,math.sin(t)*r,z) for z in [row*.22,(row+1)*.22-.012]
                   for r,t in [(.57,a),(.79,a),(.79,b),(.57,b)]]
            mesh('well_masonry',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
                 'stone_light' if (j+row)%3 else 'stone')
    for x in [-.63,.63]:
        box('roof_post',(x,0,1.18),(.14,.16,1.72))
    beam('winch',(-.76,0,1.15),(.85,0,1.15),.065,'wood_dark',8)
    beam('crank',(.85,0,1.15),(.85,0,.92),.037,'iron')
    beam('handle',(.85,0,.92),(1.02,0,.92),.035,'wood')
    beam('rope',(0,0,.3),(0,0,1.15),.014,'rope')
    bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=.1,radius2=.15,depth=.24,location=(0,0,.65))
    bpy.context.object.data.materials.append(M['wood']);bpy.context.object.name='bucket'
    for side in [-1,1]:
        for row in range(3):
            y0,y1=side*row*.25,side*(row+1)*.25
            z0,z1=2.25-row*.16,2.25-(row+1)*.16
            for j in range(6):
                x=-.93+j*.31
                tile=mesh('terracotta_roof_tile',[(x,y0,z0),(x+.30,y0,z0),(x+.30,y1,z1),(x,y1,z1)],[(0,1,2,3)],'tile')
                mod=tile.modifiers.new('tile_thickness','SOLIDIFY');mod.thickness=.035
                bpy.context.view_layer.objects.active=tile;bpy.ops.object.modifier_apply(modifier=mod.name)
    beam('ridge',(-.98,0,2.25),(.98,0,2.25),.065,'tile',5)


def cart():
    for j in range(6):
        box('bed_plank',(-.5+j*.2,0,.66),(.19,1.65,.07),'wood_light')
    for x in [-.61,.61]:
        for row in range(3):
            box('side_board',(x,0,.8+row*.14),(.065,1.78,.13),'wood')
        for y in [-.82,.82]:
            box('corner_post',(x,y,.88),(.12,.12,.72),'wood_light')
            ico('corner_bolt',(x*1.1,y,.95),(.025,.035,.035),'iron')
        box('handle',(x,-1.62,.56),(.085,1.75,.095),'wood_light')
    for y in [-.85,.85]:
        for row in range(3):
            box('end_board',(0,y,.8+row*.14),(1.25,.06,.13),'wood')
    beam('axle',(-.95,0,.48),(.95,0,.48),.065,'iron')
    for side in [-1,1]:
        x=side*.81
        def wheel():
            bpy.ops.mesh.primitive_torus_add(major_segments=16,minor_segments=4,location=(x,0,.48),major_radius=.45,minor_radius=.048,rotation=(0,math.pi/2,0))
            bpy.context.object.name='iron_rim';bpy.context.object.data.materials.append(M['iron'])
            beam('hub',(x-.09,0,.48),(x+.09,0,.48),.115,'wood_dark',8)
            for j in range(8):
                a=j*math.tau/8
                beam('spoke',(x,0,.48),(x,math.sin(a)*.43,.48+math.cos(a)*.43),.029,'wood_light',4)
        group=pivot('Wheel_L' if side<0 else 'Wheel_R',(x,0,.48),capture(wheel));sway(group,0,1,spin=True)
    for y in [-.43,.43]:
        ico('grain_sack',(0,y,1.02),(.36,.35,.42),'wool',2)
        beam('sack_neck',(0,y,1.25),(0,y,1.47),.085,'wool',6,.14)
        bpy.ops.mesh.primitive_torus_add(major_segments=10,minor_segments=4,location=(0,y,1.33),major_radius=.09,minor_radius=.012)
        bpy.context.object.data.materials.append(M['rope']);bpy.context.object.name='sack_tie'


BUILDERS = {
    'wheat-field': (wheat, '05-wheat-field.png'),
    'plowed-field': (plowed, '06-plowed-field-v2.png'),
    'vegetable-field': (vegetables, '07-vegetable-field.png'),
    'timber-bridge': (bridge, '09-timber-bridge-v2.png'),
    'fishing-boat': (fishing_boat, '12-fishing-boat-v2.png'),
    'river-fish': (fish, '24-river-fish-v2.png'),
    'sheep': (sheep, '20-sheep.png'),
    'pine-tree': (pine, '25-pine-tree.png'),
    'berry-shrub': (shrub, '27-berry-shrub.png'),
    'reeds': (reeds, '29-reeds-v2.png'),
    'village-well': (well, '31-village-well.png'),
    'handcart': (cart, '36-handcart-v2.png'),
    'plowed-field-v2': (plowed_refined, '06-plowed-field-v2.png'),
    'wheat-field-v2': (wheat_refined, '05-wheat-field.png'),
    'plowed-field-v3': (living_soil, '06-plowed-field-v2.png'),
    'wheat-field-v3': (lambda: wheat_refined(natural=True), '05-wheat-field.png'),
    'vegetable-field-v3': (vegetables_living, '07-vegetable-field.png'),
    'berry-shrub-v4': (lambda: map_element_botany.build(sys.modules[__name__], 'berry-shrub'), '27-berry-shrub.png'),
    'apple-tree': (lambda: map_element_botany.build(sys.modules[__name__], 'apple-tree'), ''),
    'pumpkin-patch': (lambda: map_element_botany.build(sys.modules[__name__], 'pumpkin-patch'), ''),
    'sunflower-field': (lambda: map_element_botany.build(sys.modules[__name__], 'sunflower-field'), ''),
    'sheep-v5': (lambda: map_element_fauna.build(sys.modules[__name__], 'sheep'), '20-sheep.png'),
    'cow': (lambda: map_element_fauna.build(sys.modules[__name__], 'cow'), ''),
    'horse': (lambda: map_element_fauna.build(sys.modules[__name__], 'horse'), ''),
    'chicken': (lambda: map_element_fauna.build(sys.modules[__name__], 'chicken'), ''),
    'goat': (lambda: map_element_fauna.build(sys.modules[__name__], 'goat'), ''),
    'pig': (lambda: map_element_fauna.build(sys.modules[__name__], 'pig'), ''),
    'duck': (lambda: map_element_fauna.build(sys.modules[__name__], 'duck'), ''),
    'deer': (lambda: map_element_fauna.build(sys.modules[__name__], 'deer'), ''),
    'cottage': (lambda: map_element_buildings.build(sys.modules[__name__], 'cottage'), ''),
    'barn': (lambda: map_element_buildings.build(sys.modules[__name__], 'barn'), ''),
    'windmill': (lambda: map_element_buildings.build(sys.modules[__name__], 'windmill'), ''),
    'watermill': (lambda: map_element_buildings.build(sys.modules[__name__], 'watermill'), ''),
    'watchtower': (lambda: map_element_fortifications.build(sys.modules[__name__], 'watchtower'), ''),
    'castle-keep': (lambda: map_element_fortifications.build(sys.modules[__name__], 'castle-keep'), ''),
    'castle-gate': (lambda: map_element_fortifications.build(sys.modules[__name__], 'castle-gate'), ''),
    'castle-wall': (lambda: map_element_fortifications.build(sys.modules[__name__], 'castle-wall'), ''),
    'corn-field': (lambda: map_element_crops.build(sys.modules[__name__], 'corn-field'), ''),
    'rice-paddy': (lambda: map_element_crops.build(sys.modules[__name__], 'rice-paddy'), ''),
    'vineyard': (lambda: map_element_crops.build(sys.modules[__name__], 'vineyard'), ''),
    'cotton-field': (lambda: map_element_crops.build(sys.modules[__name__], 'cotton-field'), ''),
    'oak-tree': (lambda: map_element_trees.build(sys.modules[__name__], 'oak-tree'), ''),
    'birch-tree': (lambda: map_element_trees.build(sys.modules[__name__], 'birch-tree'), ''),
    'willow-tree': (lambda: map_element_trees.build(sys.modules[__name__], 'willow-tree'), ''),
    'palm-tree': (lambda: map_element_trees.build(sys.modules[__name__], 'palm-tree'), ''),
    'cactus': (lambda: map_element_understory.build(sys.modules[__name__], 'cactus'), ''),
    'fern': (lambda: map_element_understory.build(sys.modules[__name__], 'fern'), ''),
    'mushrooms': (lambda: map_element_understory.build(sys.modules[__name__], 'mushrooms'), ''),
    'lily-pad': (lambda: map_element_understory.build(sys.modules[__name__], 'lily-pad'), ''),
    'bamboo': (lambda: map_element_meadow.build(sys.modules[__name__], 'bamboo'), ''),
    'wildflowers': (lambda: map_element_meadow.build(sys.modules[__name__], 'wildflowers'), ''),
    'potato-field': (lambda: map_element_meadow.build(sys.modules[__name__], 'potato-field'), ''),
    'pine-tree-v4': (lambda: map_element_conifer_reed.build(sys.modules[__name__], 'pine-tree'), ''),
    'reeds-v4': (lambda: map_element_conifer_reed.build(sys.modules[__name__], 'reeds'), ''),
    'grassland': (lambda: map_element_landforms.build(sys.modules[__name__], 'grassland'), ''),
    'rolling-hills': (lambda: map_element_landforms.build(sys.modules[__name__], 'rolling-hills'), ''),
    'rocky-mountain': (lambda: map_element_landforms.build(sys.modules[__name__], 'rocky-mountain'), ''),
    'snow-peak': (lambda: map_element_landforms.build(sys.modules[__name__], 'snow-peak'), ''),
    'volcano': (lambda: map_element_landforms.build(sys.modules[__name__], 'volcano'), ''),
    'lava-field': (lambda: map_element_landforms.build(sys.modules[__name__], 'lava-field'), ''),
    'sand-dunes': (lambda: map_element_landforms.build(sys.modules[__name__], 'sand-dunes'), ''),
    'desert-oasis': (lambda: map_element_landforms.build(sys.modules[__name__], 'desert-oasis'), ''),
    'farmer': (lambda: map_element_people.build(sys.modules[__name__], 'farmer'), ''),
    'fisher': (lambda: map_element_people.build(sys.modules[__name__], 'fisher'), ''),
    'woodcutter': (lambda: map_element_people.build(sys.modules[__name__], 'woodcutter'), ''),
    'merchant': (lambda: map_element_people.build(sys.modules[__name__], 'merchant'), ''),
    'dirt-road': (lambda: map_element_routes.build(sys.modules[__name__], 'dirt-road'), ''),
    'stone-road': (lambda: map_element_routes.build(sys.modules[__name__], 'stone-road'), ''),
    'asphalt-road': (lambda: map_element_routes.build(sys.modules[__name__], 'asphalt-road'), ''),
    'rail-track': (lambda: map_element_routes.build(sys.modules[__name__], 'rail-track'), ''),
    'rickshaw': (lambda: map_element_transport.build(sys.modules[__name__], 'rickshaw'), ''),
    'bicycle': (lambda: map_element_transport.build(sys.modules[__name__], 'bicycle'), ''),
    'early-car': (lambda: map_element_transport.build(sys.modules[__name__], 'early-car'), ''),
    'freight-wagon': (lambda: map_element_transport.build(sys.modules[__name__], 'freight-wagon'), ''),
    'rider': (lambda: map_element_mounted.build(sys.modules[__name__], 'rider'), ''),
    'horse-cart': (lambda: map_element_mounted.build(sys.modules[__name__], 'horse-cart'), ''),
    'steam-locomotive': (lambda: map_element_steam.build(sys.modules[__name__]), ''),
    'sailboat': (lambda: map_element_vessels.build(sys.modules[__name__], 'sailboat'), ''),
    'river-barge': (lambda: map_element_vessels.build(sys.modules[__name__], 'river-barge'), ''),
    'stable': (lambda: map_element_workshops.build(sys.modules[__name__], 'stable'), ''),
    'blacksmith': (lambda: map_element_workshops.build(sys.modules[__name__], 'blacksmith'), ''),
    'market-hall': (lambda: map_element_workshops.build(sys.modules[__name__], 'market-hall'), ''),
    'train-station': (lambda: map_element_industry.build(sys.modules[__name__], 'train-station'), ''),
    'factory': (lambda: map_element_industry.build(sys.modules[__name__], 'factory'), ''),
    'stone-bridge': (lambda: map_element_bridges.build(sys.modules[__name__], 'stone-bridge'), ''),
    'steel-bridge': (lambda: map_element_bridges.build(sys.modules[__name__], 'steel-bridge'), ''),
    'aqueduct': (lambda: map_element_hydraulics.build(sys.modules[__name__], 'aqueduct'), ''),
    'irrigation-channel': (lambda: map_element_hydraulics.build(sys.modules[__name__], 'irrigation-channel'), ''),
    'inn': (lambda: map_element_civic.build(sys.modules[__name__], 'inn'), ''),
    'chapel': (lambda: map_element_civic.build(sys.modules[__name__], 'chapel'), ''),
    'wetland': (lambda: map_element_riparian.build(sys.modules[__name__], 'wetland'), ''),
    'river-bend': (lambda: map_element_riparian.build(sys.modules[__name__], 'river-bend'), ''),
}


def consolidate():
    # Keep animated pivots separate; combine their static children to limit draw calls.
    groups = {}
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH':
            groups.setdefault(obj.parent, []).append(obj)
    for parent, objects in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects)>1:
            bpy.ops.object.join()
        obj = bpy.context.object
        obj.name = (parent.name if parent else 'Static') + '_mesh'
        # Remove duplicate slots created by joining repeated plant/plank objects.
        bpy.ops.object.material_slot_remove_unused()


def build(asset_id):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Previous workers' stashed actions must not leak into the next asset export.
    for action in bpy.data.actions:
        if action.use_fake_user and action.users==1:action.use_fake_user=False
    for datablocks in [bpy.data.meshes,bpy.data.materials,bpy.data.actions]:
        for item in list(datablocks):
            if item.users == 0:
                datablocks.remove(item)
    RNG.seed(20261012)
    palette()
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=73
    BUILDERS[asset_id][0]()
    scene.frame_set(0 if asset_id in map_element_people.KINDS else 1)
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(asset_id+'.blend')),compress=True)
    consolidate()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT/(asset_id+'.glb')),export_format='GLB',use_selection=True,
                              export_apply=asset_id!='mushrooms',export_animations=True,export_animation_mode='ACTIONS' if asset_id in map_element_people.KINDS else 'SCENE',
                              export_extras=True)
    objects=[o for o in scene.objects if o.type=='MESH']
    triangles=0
    for obj in objects:
        obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
    coords=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
    return {'id':asset_id,'reference':BUILDERS[asset_id][1], 'triangles':triangles,
            'meshObjects':len(objects),'animatedPivots':[o.name for o in scene.objects if o.animation_data],
            'boundsMeters':[[round(min(v[i] for v in coords),4) for i in range(3)],
                            [round(max(v[i] for v in coords),4) for i in range(3)]],
            'glbBytes':(OUT/(asset_id+'.glb')).stat().st_size}


def main():
    args=argparse.ArgumentParser()
    args.add_argument('--assets',nargs='+',choices=list(BUILDERS),default=list(BUILDERS))
    opts=args.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    OUT.mkdir(parents=True,exist_ok=True);SOURCE.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0
    results=[build(name) for name in opts.assets]
    manifest=OUT/'manifest.json'
    previous=json.loads(manifest.read_text())['assets'] if manifest.exists() else []
    merged={a['id']:a for a in previous};merged.update({a['id']:a for a in results})
    manifest.write_text(json.dumps({'version':1,'style':'C faceted low-poly','status':'first-modeling-pass',
                                   'units':'meters','sourceUp':'Z','gltfUp':'Y','sourceFront':'-Y',
                                   'animation':'Object-pivot clips, metadata-driven lifecycles and skinned human action clips',
                                   'assets':list(merged.values())},indent=2)+'\n',encoding='utf-8')
    print('ELEMENT_KIT_COMPLETE',json.dumps(results))


if __name__=='__main__':
    main()
