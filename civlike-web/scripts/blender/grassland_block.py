"""Textured meadow diorama. Both LODs share the same seeded scatter layout."""

import math
import random

import bpy
import numpy as np
from mathutils import Vector, noise


RADIUS = 1.12
BASE_Z = -0.21


def surface_z(x, y, phase):
    return (0.12 + 0.024 * noise.noise_vector(Vector((x * 2.3, y * 2.3, phase)))[0]
            + 0.006 * noise.noise_vector(Vector((x * 10, y * 10, phase)))[1])


def outline(t):
    edge = int(t) % 6
    frac = t - math.floor(t)
    a = math.pi / 6 + edge * math.tau / 6
    b = a + math.tau / 6
    return (RADIUS * ((1 - frac) * math.cos(a) + frac * math.cos(b)),
            RADIUS * ((1 - frac) * math.sin(a) + frac * math.sin(b)))


def scatter(seed, count, margin=0.92):
    rng = random.Random(seed)
    points = []
    while len(points) < count:
        x, y = rng.uniform(-RADIUS, RADIUS), rng.uniform(-RADIUS, RADIUS)
        if all(x * math.cos(i * math.tau / 6) + y * math.sin(i * math.tau / 6)
               < RADIUS * math.cos(math.pi / 6) * margin for i in range(6)):
            points.append((x, y))
    return points


def mesh_object(name, vertices, faces, materials, uv_faces=None, colors=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    for mat in materials:
        mesh.materials.append(mat)
    if uv_faces is not None:
        uv = mesh.uv_layers.new(name="UVMap")
        for polygon, coords in zip(mesh.polygons, uv_faces):
            for loop, coord in zip(polygon.loop_indices, coords):
                uv.data[loop].uv = coord
    if colors is not None:
        attribute = mesh.color_attributes.new(name="BladeTint", type="FLOAT_COLOR", domain="POINT")
        attribute.data.foreach_set("color", np.asarray(colors, dtype=np.float32).ravel())
    return obj


def flat_material(name, color, vertex_color=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.88
    if vertex_color:
        node = mat.node_tree.nodes.new("ShaderNodeVertexColor")
        node.layer_name = "BladeTint"
        mat.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def data_image(name, rgba, path):
    height, width = rgba.shape[:2]
    image = bpy.data.images.new(name, width=width, height=height, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(np.asarray(rgba, dtype=np.float32).ravel())
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    image.pack()
    return image


def textured_material(name, source, texture_root, detailed):
    lod = "lod0" if detailed else "lod1"
    image = bpy.data.images.load(str(texture_root / source), check_existing=True)
    image.scale(1024 if detailed else 512, 1024 if detailed else 512)
    image.pack()
    pixels = np.empty(len(image.pixels), dtype=np.float32)
    image.pixels.foreach_get(pixels)
    pixels = pixels.reshape(image.size[1], image.size[0], 4)
    height = pixels[:, :, :3].dot(np.array([0.2126, 0.7152, 0.0722]))
    # Luminance-derived microrelief, not measured photogrammetry displacement.
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 1.4
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 1.4
    normal = np.stack((-dx, -dy, np.ones_like(height)), axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    rgba = np.concatenate((normal * 0.5 + 0.5, np.ones((*height.shape, 1))), axis=2)
    normal_image = data_image(f"{name}_{lod}_normal", rgba, texture_root / f"{name}-{lod}-normal.png")
    roughness = np.clip(0.93 - height * 0.15, 0.72, 0.96)
    rgba = np.stack((roughness, roughness, roughness, np.ones_like(height)), axis=2)
    rough_image = data_image(f"{name}_{lod}_roughness", rgba, texture_root / f"{name}-{lod}-roughness.png")
    mat = flat_material(name, (1, 1, 1))
    tree = mat.node_tree
    bsdf = tree.nodes.get("Principled BSDF")
    for bitmap, socket in ((image, "Base Color"), (rough_image, "Roughness")):
        node = tree.nodes.new("ShaderNodeTexImage")
        node.image = bitmap
        tree.links.new(node.outputs["Color"], bsdf.inputs[socket])
    node = tree.nodes.new("ShaderNodeTexImage")
    node.image = normal_image
    normal_node = tree.nodes.new("ShaderNodeNormalMap")
    normal_node.inputs["Strength"].default_value = 0.7
    tree.links.new(node.outputs["Color"], normal_node.inputs["Color"])
    tree.links.new(normal_node.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def create_core(detailed, phase, meadow, soil):
    segments = 192 if detailed else 96
    rings = 32 if detailed else 16
    side_rows = 20 if detailed else 10
    vertices = [(0, 0, surface_z(0, 0, phase))]
    faces, uvs, material_ids = [], [], []

    def face(indices, uv, material_id):
        faces.append(indices)
        uvs.append(uv)
        material_ids.append(material_id)

    def top_uv(index):
        x, y, _ = vertices[index]
        return (0.5 + x / 2.3, 0.5 + y / 2.3)

    for ring in range(1, rings + 1):
        fraction = ring / rings
        for j in range(segments):
            x, y = outline(j * 6 / segments)
            x, y = x * fraction, y * fraction
            vertices.append((x, y, surface_z(x, y, phase)))
        start = 1 + (ring - 1) * segments
        for j in range(segments):
            current, following = start + j, start + (j + 1) % segments
            indices = (0, current, following) if ring == 1 else (
                current - segments, current, following, following - segments)
            face(indices, [top_uv(i) for i in indices], 0)

    # Reuse the top perimeter vertices; there is no floating cap or gap at the lip.
    edge_start = 1 + (rings - 1) * segments
    previous_start = edge_start
    for row in range(1, side_rows + 1):
        v = row / side_rows
        start = len(vertices)
        for j in range(segments):
            x, y, top = vertices[edge_start + j]
            relief = noise.noise_vector(Vector((x * 25, y * 25, v * 7 + phase)))[0]
            taper = math.sin(v * math.pi) * 0.012 * relief - 0.014 * v
            vertices.append((x * (1 + taper), y * (1 + taper), top * (1 - v) + BASE_Z * v))
        for j in range(segments):
            following = (j + 1) % segments
            # Two repeated scans around six faces, preserving a fine rock scale.
            u0, u1 = j * 2 / segments, (j + 1) * 2 / segments
            face((previous_start + j, start + j, start + following, previous_start + following),
                 [(u0, 1 - (row - 1) / side_rows), (u0, 1 - v),
                  (u1, 1 - v), (u1, 1 - (row - 1) / side_rows)], 1)
        previous_start = start
    face(tuple(reversed(range(previous_start, previous_start + segments))),
         [top_uv(i) for i in reversed(range(previous_start, previous_start + segments))], 1)
    obj = mesh_object("terrain_core", vertices, faces, [meadow, soil], uvs)
    for polygon, mat_id in zip(obj.data.polygons, material_ids):
        polygon.material_index = mat_id
        polygon.use_smooth = True
    obj["design_version"] = "meadow-v2"


def add_blade(vertices, faces, colors, rng, x, y, z, height, width, segments):
    angle = rng.uniform(0, math.tau)
    bend = height * rng.uniform(0.4, 0.9)
    dx, dy = math.cos(angle), math.sin(angle)
    shade = rng.uniform(0.65, 1.15)
    start = len(vertices)
    for index in range(segments + 1):
        t = index / segments
        half_width = width * (1 - t) * 0.5 + 0.00008
        cx, cy = x + dx * bend * t * t, y + dy * bend * t * t
        cz = z + height * math.sin(t * math.pi * 0.72)
        for side in (-1, 1):
            vertices.append((cx - dy * half_width * side, cy + dx * half_width * side, cz))
            brightness = shade * (0.6 + t * 0.4)
            colors.append((0.22 * brightness, 0.29 * brightness, 0.058 * brightness, 1))
        if index:
            a = start + (index - 1) * 2
            faces.append((a, a + 1, a + 3, a + 2))


def create_foliage(detailed, seed, phase, leaf):
    # Eight batched ground-cover patches instead of hundreds of draw calls.
    positions = scatter(seed + 201, 1600, 0.99)
    for patch in range(8):
        vertices, faces, colors = [], [], []
        for index in range(patch, len(positions), 8):
            rng = random.Random(seed + 4001 + index)
            x, y = positions[index]
            height = rng.uniform(0.013, 0.035)
            if not detailed and index % 3:
                continue
            add_blade(vertices, faces, colors, rng, x, y, surface_z(x, y, phase) - 0.002,
                      height, rng.uniform(0.002, 0.0035), 3 if detailed else 2)
        mesh_object(f"meadow_cover_{patch}", vertices, faces, [leaf], colors=colors)

    positions = scatter(seed + 221, 44)
    # Some larger clumps break the perimeter; most of the ground stays open.
    positions += [tuple(v * 0.98 for v in outline(i * 6 / 24)) for i in range(24)]
    for index, (x, y) in enumerate(positions):
        rng = random.Random(seed + 7011 + index)
        vertices, faces, colors = [], [], []
        for blade in range(12):
            height = rng.uniform(0.045, 0.105)
            px, py = rng.uniform(-0.012, 0.012), rng.uniform(-0.012, 0.012)
            width = rng.uniform(0.004, 0.007)
            if not detailed and blade % 2:
                continue
            add_blade(vertices, faces, colors, rng, px, py, 0, height, width, 5 if detailed else 3)
        obj = mesh_object(f"grass_clump_{index:03}", vertices, faces, [leaf], colors=colors)
        obj.location = (x, y, surface_z(x, y, phase) - 0.004)


def create_stones(detailed, seed, phase, soil):
    for index, (x, y) in enumerate(scatter(seed + 800, 35)):
        rng = random.Random(seed + 1800 + index)
        radius = rng.uniform(0.012, 0.028) if index > 5 else rng.uniform(0.035, 0.055)
        if not detailed and index > 12:
            continue
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2 if detailed else 1, radius=1)
        obj = bpy.context.object
        obj.name = f"surface_stone_{index:03}"
        obj.location = (x, y, surface_z(x, y, phase) + radius * 0.10)
        for vertex in obj.data.vertices:
            vertex.co *= rng.uniform(0.82, 1.16)
            vertex.co.x *= radius
            vertex.co.y *= radius * 0.78
            vertex.co.z *= radius * 0.60
        obj.rotation_euler.z = rng.uniform(0, math.tau)
        obj.data.materials.append(soil)
        uv = obj.data.uv_layers.new(name="UVMap")
        offset_u, offset_v = rng.random() * 0.7, rng.random() * 0.35
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
            for loop in polygon.loop_indices:
                co = obj.data.vertices[obj.data.loops[loop].vertex_index].co
                uv.data[loop].uv = (offset_u + co.x * 2, offset_v + 0.15 + co.y * 2)


def create_flowers(detailed, seed, phase):
    mats = [flat_material("petal_ivory", (0.8, 0.76, 0.60)),
            flat_material("petal_ochre", (0.7, 0.43, 0.035)),
            flat_material("petal_lilac", (0.39, 0.20, 0.46)),
            flat_material("flower_center", (0.4, 0.25, 0.025)),
            flat_material("flower_stem", (0.07, 0.13, 0.025))]
    for index, (x, y) in enumerate(scatter(seed + 8100, 16)):
        rng = random.Random(seed + 9100 + index)
        vertices, faces, material_ids = [], [], []
        for flower in range(5 if detailed else 2):
            px, py = rng.uniform(-0.055, 0.055), rng.uniform(-0.055, 0.055)
            h = rng.uniform(0.02, 0.05)
            radius = rng.uniform(0.004, 0.007)
            start = len(vertices)
            vertices.extend([(px - 0.0008, py, 0), (px + 0.0008, py, 0),
                             (px + 0.0008, py, h), (px - 0.0008, py, h)])
            faces.append((start, start + 1, start + 2, start + 3))
            material_ids.append(4)
            for petal in range(5):
                a = petal * math.tau / 5
                dx, dy = math.cos(a), math.sin(a)
                start = len(vertices)
                vertices.extend([(px, py, h),
                                 (px + dx * radius * 0.5 - dy * radius * 0.32,
                                  py + dy * radius * 0.5 + dx * radius * 0.32, h + 0.001),
                                 (px + dx * radius, py + dy * radius, h + 0.002),
                                 (px + dx * radius * 0.5 + dy * radius * 0.32,
                                  py + dy * radius * 0.5 - dx * radius * 0.32, h + 0.001)])
                faces.append((start, start + 1, start + 2, start + 3))
                material_ids.append(index % 3)
            start = len(vertices)
            vertices.extend([(px + math.cos(k * math.tau / 6) * radius * 0.25,
                              py + math.sin(k * math.tau / 6) * radius * 0.25, h + 0.0018) for k in range(6)])
            faces.append(tuple(range(start, start + 6)))
            material_ids.append(3)
        obj = mesh_object(f"wildflower_{index:03}", vertices, faces, mats)
        obj.location = (x, y, surface_z(x, y, phase))
        for polygon, material_id in zip(obj.data.polygons, material_ids):
            polygon.material_index = material_id


def create_grassland_block(detailed, seed, texture_root):
    phase = (seed % 997) / 113
    meadow = textured_material("meadow_surface", "grassland-meadow-source.png", texture_root, detailed)
    soil = textured_material("soil_cutaway", "grassland-cutaway-source.png", texture_root, detailed)
    leaf = flat_material("meadow_leaf", (1, 1, 1), vertex_color=True)
    create_core(detailed, phase, meadow, soil)
    create_foliage(detailed, seed, phase, leaf)
    create_stones(detailed, seed, phase, soil)
    create_flowers(detailed, seed, phase)
    bpy.context.scene["grassland_design_version"] = "meadow-v2"
    bpy.context.scene["generation_seed"] = seed
