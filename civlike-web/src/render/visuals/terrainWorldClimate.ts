import * as THREE from 'three'
import { WATER_LEVEL, smoothstep, type GroundSample } from './terrainWorld'

export const TERRAIN_BIOMES = [
  { id: 'meadow', label: '花甸', color: '#a4b95b' },
  { id: 'grassland', label: '草原', color: '#83a532' },
  { id: 'broadleaf', label: '阔叶林', color: '#4e793c' },
  { id: 'conifer', label: '针叶林', color: '#315d53' },
  { id: 'wetland', label: '湿地', color: '#628e78' },
  { id: 'steppe', label: '旱草原', color: '#c4b256' },
  { id: 'dunes', label: '沙丘', color: '#e2c08a' },
  { id: 'badlands', label: '红岩荒地', color: '#b86e52' },
  { id: 'tundra', label: '苔原', color: '#a4ac9b' },
  { id: 'hills', label: '丘陵', color: '#96a367' },
  { id: 'alpine', label: '高山', color: '#929c9e' },
  { id: 'shore', label: '沙岸', color: '#e8d6a3' },
  { id: 'shallows', label: '浅水', color: '#69bcba' },
  { id: 'water', label: '深水', color: '#19849e' },
] as const
export type TerrainBiome = typeof TERRAIN_BIOMES[number]['id']
export type TerrainSeason = { id: string; label: string; snow: number; foliage: number; bloom: number; dry: number; ice: number; litter: number; leaves: string[] }
export const TERRAIN_SEASONS = [
  { id: 'thaw', label: '初春', snow: 0.25, foliage: 0.4, bloom: 0.3, dry: 0.15, ice: 0.22, litter: 0, leaves: ['#7d9c49','#aac56a','#739346'] },
  { id: 'bloom', label: '暮春', snow: 0, foliage: 1, bloom: 1, dry: 0, ice: 0, litter: 0, leaves: ['#608c3b','#8eb84e','#accb68','#44734b'] },
  { id: 'green', label: '初夏', snow: 0, foliage: 1, bloom: 0.62, dry: 0.04, ice: 0, litter: 0, leaves: ['#285443','#396445','#597e32','#719334'] },
  { id: 'dry', label: '盛夏', snow: 0, foliage: 0.95, bloom: 0.25, dry: 0.4, ice: 0, litter: 0, leaves: ['#446745','#64803c','#7b9143'] },
  { id: 'harvest', label: '初秋', snow: 0, foliage: 0.95, bloom: 0.1, dry: 0.45, ice: 0, litter: 0.3, leaves: ['#ba953f','#b7a64e','#7b8b40','#ba6c36'] },
  { id: 'rust', label: '深秋', snow: 0, foliage: 0.42, bloom: 0, dry: 0.78, ice: 0, litter: 0.95, leaves: ['#d17a36','#a44e37','#d7ac4c','#aa743e'] },
  { id: 'frost', label: '初冬', snow: 0.5, foliage: 0.12, bloom: 0, dry: 0.85, ice: 0.58, litter: 0.45, leaves: ['#a08b67','#ae9369','#9b7659'] },
  { id: 'snow', label: '深冬', snow: 1, foliage: 0, bloom: 0, dry: 1, ice: 1, litter: 0.12, leaves: ['#947a5c','#b1a083','#82745b'] },
] satisfies TerrainSeason[]
export function getTerrainSeason(id: string | null): TerrainSeason {
  return TERRAIN_SEASONS.find((season) => season.id === id) ?? TERRAIN_SEASONS[1]
}
export function terrainBiome(s: GroundSample): TerrainBiome {
  if (s.height < WATER_LEVEL) return s.wetland > 0.3 || s.height > -0.28 ? 'shallows' : 'water'
  if (s.rock > 0.45) return 'alpine'
  if (s.shore < 0.42) return 'shore'
  if (s.wetland > 0.38) return 'wetland'
  if (s.desert > 0.48) return 'dunes'
  if (s.badlands > 0.48) return 'badlands'
  if (s.cold > 0.76) return 'tundra'
  if (s.pine > 0.45) return 'conifer'
  if (s.forest > 0.45) return 'broadleaf'
  if (s.height > 0.8) return 'hills'
  if (s.meadow > 0.48) return 'meadow'
  if (s.dry > 0.48) return 'steppe'
  return 'grassland'
}
export function snowCover(s: GroundSample, season: TerrainSeason): number {
  const climate = Math.max(s.cold, smoothstep(0.6, 3, s.height))
  return smoothstep(0.28, 0.8, season.snow * 0.92 + climate * 0.45 + s.patch * 0.06)
    * (1 - s.desert * 0.96) * (1 - s.badlands * 0.72) * smoothstep(WATER_LEVEL, WATER_LEVEL + 0.09, s.height)
}
const colors = {
  grass: new THREE.Color('#83a532'), forest: new THREE.Color('#536f2c'), dry: new THREE.Color('#c7b356'),
  sand: new THREE.Color('#efda9c'), rock: new THREE.Color('#737c89'), peak: new THREE.Color('#c3c6c4'),
  wet: new THREE.Color('#628e78'), desert: new THREE.Color('#e2c08a'), badlands: new THREE.Color('#b86e52'),
  tundra: new THREE.Color('#a4ac9b'), snow: new THREE.Color('#ebf3f3'), litter: new THREE.Color('#ad713c'),
}
export function terrainGroundColor(s: GroundSample, season: TerrainSeason): THREE.Color {
  const color = colors.grass.clone().lerp(colors.forest, s.forest * 0.6)
    .lerp(colors.dry, Math.min(1, s.dry + season.dry * 0.55))
    .lerp(colors.litter, s.forest * season.litter * 0.6)
    .lerp(colors.wet, s.wetland * 0.86).lerp(colors.tundra, s.cold * 0.78)
    .lerp(colors.desert, s.desert).lerp(colors.badlands, s.badlands * 0.92)
  color.multiplyScalar(1 + s.patch * 0.08)
  color.lerp(colors.sand, 1 - smoothstep(0.12, 0.5, s.shore))
  color.lerp(colors.rock, s.rock).lerp(colors.peak, smoothstep(1.5, 3.6, s.height) * s.rock * 0.75)
  return color.lerp(colors.snow, snowCover(s, season))
}
