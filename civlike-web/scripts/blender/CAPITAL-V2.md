# Capital tile V2

This model draft uses six reusable mesh templates: window, banner, roof,
wall, tower and gate. Towers and gates reuse the smaller templates; the
capital reuses those same objects. Separate GLBs use the `capital-v2-`
prefix, leaving the previous kit available for comparison.

The foundation is 0.62 units wide on a 1.732 by 2 unit hex tile. All
placement coordinates in the generator are scaled by 0.1 at the end.
Blender source is Z-up; GLB export uses the standard glTF axis conversion.
Stone joints use a shared packed 256px albedo. Silhouette details, slate
courses, arch voussoirs and battlements use geometry.

Run from the civlike-web directory in PowerShell:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe' --background --factory-startup --python-exit-code 1 --python scripts/blender/city_block_v2.py
& 'C:\Program Files\Blender Foundation\Blender 4.5\blender.exe' --background --factory-startup --python-exit-code 1 --python scripts/blender/verify_city_block_v2.py
```

The first command updates the main `.blend`, both main GLBs, six module
GLBs, the kit `.blend`, stone PNG, and three `artifacts/capital-v2-*.png`
previews. The second checks GLB headers, embedded textures, LOD triangle
reduction and round-trip dimensions, then renders the imported GLB.

The existing `build-terrain-assets.mjs buildable-city-center` entry also
uses V2. Use the dedicated generator for the component exports and the
review camera setup.

LOD0 currently contains approximately 37k unique-mesh triangles; LOD1
approximately 6.5k. Both preserve the building layout. Many separate nodes
remain for editing. This is a visual review asset, not a verified map-wide
rendering budget: batching or merging per module/material and in-game
performance measurements remain necessary before mass placement.
