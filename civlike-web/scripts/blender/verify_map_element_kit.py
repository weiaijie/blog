"""Read-only validation of exported GLBs and editable Blender sources."""
import json
import math
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
assets = ROOT / 'src/render/assets'
manifest = json.loads((assets / 'elements/manifest.json').read_text(encoding='utf-8'))
results = []
for asset in manifest['assets']:
    with bpy.data.libraries.load(str(assets / 'source/elements' / (asset['id'] + '.blend'))) as (source, _):
        source_objects = len(source.objects)
        assert source_objects > 1, asset['id'] + ': missing editable components'
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(assets / 'elements' / (asset['id'] + '.glb')))
    bpy.context.scene.frame_set(0)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert meshes, asset['id'] + ': empty mesh'
    triangles = 0
    for obj in meshes:
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        assert all(math.isfinite(c) for v in obj.data.vertices for c in v.co)
    assert triangles == asset['triangles'], asset['id'] + ': triangle count changed'
    results.append({'id': asset['id'], 'sourceObjects': source_objects, 'roundTripTriangles': triangles})
out = ROOT / 'artifacts/map-elements/blender-roundtrip.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'assets': results, 'passed': len(results)}, indent=2) + '\n', encoding='utf-8')
print('ROUNDTRIP_VERIFIED', len(results))
