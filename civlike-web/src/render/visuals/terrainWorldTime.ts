import { Color } from 'three'
import { seededRandom, smoothstep } from './terrainWorld'
import { TERRAIN_SEASONS, type TerrainSeason } from './terrainWorldClimate'

export const YEAR_DAYS = 360
export function initialWorldDay(seed: number, season?: string | null) {
  const index=TERRAIN_SEASONS.findIndex((s)=>s.id===season)
  const random=seededRandom(seed^0x8b271a3d)
  random(); random()
  return index>=0 ? index*45 : Math.floor(random()*YEAR_DAYS)
}

export function advanceWorldDay(day: number, delta: number, speed: number, running: boolean) {
  return day+(running?Math.max(0,delta)*Math.max(0,speed)/2:0)
}

export function worldCalendar(day: number) {
  const within=((day%YEAR_DAYS)+YEAR_DAYS)%YEAR_DAYS
  const index=Math.floor(within/45), progress=within/45-index
  return {year:Math.floor(day/YEAR_DAYS)+1,day:Math.floor(within)+1,index,progress,season:TERRAIN_SEASONS[index]}
}

export function seasonalBlend(day: number): TerrainSeason {
  const {index,progress}=worldCalendar(day)
  const a=TERRAIN_SEASONS[index], b=TERRAIN_SEASONS[(index+1)%8]
  const t=smoothstep(0.35,1,progress)
  const mix=(key:'snow'|'foliage'|'bloom'|'dry'|'ice'|'litter')=>a[key]*(1-t)+b[key]*t
  return {...a,snow:mix('snow'),foliage:mix('foliage'),bloom:mix('bloom'),dry:mix('dry'),ice:mix('ice'),litter:mix('litter'),
    leaves:Array.from({length:4},(_,i)=>`#${new Color(a.leaves[i%a.leaves.length]).lerp(new Color(b.leaves[i%b.leaves.length]),t).getHexString()}`)}
}

export type WorldCalendar = ReturnType<typeof worldCalendar>
