import terrainGrasslandLod0 from './terrain/terrain-grassland-lod0.glb?url'
import terrainHillLod0 from './terrain/terrain-hill-lod0.glb?url'
import terrainWaterLod0 from './terrain/terrain-water-lod0.glb?url'
import transitionShorelineLod0 from './transitions/transition-shoreline-lod0.glb?url'

export type RuntimeModelAssetId = 'terrain-grassland' | 'terrain-hill' | 'terrain-water' | 'transition-shoreline'

export const runtimeModelAssetUrls: Record<RuntimeModelAssetId, string> = {
  'terrain-grassland': terrainGrasslandLod0,
  'terrain-hill': terrainHillLod0,
  'terrain-water': terrainWaterLod0,
  'transition-shoreline': transitionShorelineLod0,
}
