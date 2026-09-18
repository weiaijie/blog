"""Round-trip the shipping GLB, check bounds and LOD, and render the imported mesh."""
import json
import struct
from pathlib import Path
import importlib.util

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('capital', Path(__file__).with_name('city_block_v2.py'))
capital = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capital)


def inspect(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    assert magic == 0x46546C67 and version == 2 and length == len(data), path
    json_length, chunk_type = struct.unpack_from('<II', data, 12)
    assert chunk_type == 0x4E4F534A
    doc = json.loads(data[20:20+json_length])
    assert not doc.get('cameras')
    triangles = sum(doc['accessors'][p['indices']]['count']//3 for m in doc['meshes'] for p in m['primitives'])
    assert all('bufferView' in im for im in doc.get('images', [])), 'Textures must be embedded'
    return {'bytes':length, 'meshTriangles':triangles, 'nodes':len(doc['nodes']), 'embeddedImages':len(doc.get('images', []))}


assets = ROOT / 'src/render/assets/buildables'
report = {}
for lod in ['lod0','lod1']:
    path = assets / ('buildable-city-center-'+lod+'.glb')
    report[lod] = inspect(path)
assert report['lod1']['meshTriangles'] < report['lod0']['meshTriangles']
for path in sorted((assets/'modules').glob('capital-v2-*.glb')):
    report[path.stem] = inspect(path)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(assets/'buildable-city-center-lod0.glb'))
objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']
corners = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
extents = [max(v[i] for v in corners)-min(v[i] for v in corners) for i in range(3)]
assert 1.7 < extents[0] < 2.1 and 1.7 < extents[1] < 2.1, extents
assert .5 < extents[2] < .8, extents
report['boundsXYZ'] = extents
report['importedMeshes'] = len(objects)
capital.setup_camera((0,0,.05),(2.7,-4,3.2),2.55,ROOT/'artifacts/capital-v2-glb-check.png')
bpy.ops.render.render(write_still=True)
(ROOT/'artifacts/capital-v2-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CAPITAL_VALIDATION_OK', json.dumps(report))
