"""Normalize two licensed Quaternius samples without rebuilding their geometry."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'src/render/assets/source/vendor/quaternius'
OUT = ROOT / 'src/render/assets/elements'
SOURCE = ROOT / 'src/render/assets/source/elements'


def import_asset(name, asset_id):
    for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
    for action in list(bpy.data.actions): bpy.data.actions.remove(action)
    original = json.loads((RAW / f'{name}.gltf').read_text(encoding='utf-8'))
    bpy.ops.import_scene.gltf(filepath=str(RAW / f'{name}.gltf'))
    root = bpy.data.objects.new('LicensedAssetRoot', None)
    bpy.context.collection.objects.link(root)
    root['licensedAsset'] = asset_id
    root['assetAuthor'] = 'Quaternius'
    root['assetLicense'] = 'CC0-1.0'
    for obj in list(bpy.context.scene.objects):
        if obj != root and obj.parent is None:
            world = obj.matrix_world.copy()
            obj.parent = root
            obj.matrix_world = world
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.frame_set(0)
    bone_shapes = {pose.custom_shape for obj in scene.objects if obj.type=='ARMATURE' for pose in obj.pose.bones if pose.custom_shape}
    mesh_objects = [obj for obj in scene.objects if obj.type == 'MESH' and obj not in bone_shapes]
    minimum, maximum = Vector((1e6, 1e6, 1e6)), Vector((-1e6, -1e6, -1e6))
    rigs = [obj for obj in scene.objects if obj.type == 'ARMATURE']
    for rig in rigs:
        if not rig.animation_data: continue
        for track in rig.animation_data.nla_tracks: track.mute = True
    actions = list(bpy.data.actions)
    clip_bounds = {}
    for action in actions:
        clip_minimum, clip_maximum = Vector((1e6,1e6,1e6)), Vector((-1e6,-1e6,-1e6))
        for rig in rigs:
            rig.animation_data.action = action
        first, last = action.frame_range
        for frame in range(int(first), int(last)+1, 2):
            scene.frame_set(frame)
            graph = bpy.context.evaluated_depsgraph_get()
            for obj in mesh_objects:
                evaluated = obj.evaluated_get(graph)
                for corner in evaluated.bound_box:
                    point = evaluated.matrix_world @ Vector(corner)
                    for axis in range(3):
                        minimum[axis] = min(minimum[axis], point[axis])
                        maximum[axis] = max(maximum[axis], point[axis])
                        clip_minimum[axis] = min(clip_minimum[axis], point[axis])
                        clip_maximum[axis] = max(clip_maximum[axis], point[axis])
        clip_bounds[action.name] = {'min':[clip_minimum.x-.04,clip_minimum.z-.04,-clip_maximum.y-.04],
                                    'max':[clip_maximum.x+.04,clip_maximum.z+.04,-clip_minimum.y+.04]}
    root['animationBoundsMin'] = [minimum.x-.04, minimum.z-.04, -maximum.y-.04]
    root['animationBoundsMax'] = [maximum.x+.04, maximum.z+.04, -minimum.y+.04]
    root['clipBounds'] = json.dumps(clip_bounds)
    for rig in rigs: rig.animation_data.action = None
    scene.frame_set(0)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE / f'{asset_id}.blend'), compress=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT / f'{asset_id}.glb'), export_format='GLB',
                              use_selection=True, export_animations=True, export_animation_mode='ACTIONS',
                              export_frame_range=False, export_extras=True)
    triangles = 0
    for obj in mesh_objects:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
    row = {'id':asset_id,'reference':'','triangles':triangles,'meshObjects':len(mesh_objects),
           'animatedPivots':[obj.name for obj in rigs],
           'boundsMeters':[[round(minimum[i], 4) for i in range(3)], [round(maximum[i], 4) for i in range(3)]],
           'glbBytes':(OUT / f'{asset_id}.glb').stat().st_size}
    exported = (OUT / f'{asset_id}.glb').read_bytes()
    length = int.from_bytes(exported[12:16], 'little')
    data = json.loads(exported[20:20+length])
    expected = sorted(a['name'] for a in original['animations'])
    actual = sorted(a['name'] for a in data['animations'])
    assert actual == expected, (asset_id, expected, actual)
    return row


OUT.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)
rows = [import_asset('Farmer', 'farmer-v3'), import_asset('Horse', 'horse-v3')]
path = OUT / 'manifest.json'
manifest = json.loads(path.read_text(encoding='utf-8'))
assets = {row['id']:row for row in manifest['assets']}
assets.update({row['id']:row for row in rows})
manifest['assets'] = list(assets.values())
path.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
print('LICENSED_ASSETS_IMPORTED', json.dumps(rows))
