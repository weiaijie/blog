import createGraph from 'ngraph.graph'
import { aStar } from 'ngraph.path'
import { CatmullRomCurve3, Vector3 } from 'three'
import { WATER_LEVEL, seededRandom, type GroundPoint, type GroundSample, type TerrainField } from './terrainWorld'

export type SurfaceSampler = (x: number, z: number) => GroundSample | null
export type PlaceKind = 'town' | 'village' | 'farmstead' | 'lumber' | 'quarry' | 'ruins' | 'harbor' | 'lookout'
export type WorldPlace = { id: string; label: string; kind: PlaceKind; center: GroundSample; radius: number }
export type WorldRoad = { points: GroundSample[]; bridge: boolean; from: string; to: string }
export type WorldBuilding = { placeId: string; center: GroundSample; rotation: number; size: number; kind: 'house' | 'barn' | 'hall' | 'mill' | 'tower' | 'ruin' | 'logs'; variant: number }
export type WorldFarm = { center: GroundSample; width: number; depth: number; crop: number }
export type CivilizationPlan = { places: WorldPlace[]; roads: WorldRoad[]; buildings: WorldBuilding[]; farms: WorldFarm[]; docks: { bank: GroundSample; end: GroundSample }[] }

const distance = (a: GroundPoint, b: GroundPoint) => Math.hypot(a.x - b.x, a.z - b.z)
const key = (p: GroundPoint) => `${p.x},${p.z}`

export function segmentDistance(p: GroundPoint, a: GroundPoint, b: GroundPoint) {
  const dx = b.x - a.x, dz = b.z - a.z
  const t = Math.max(0, Math.min(1, ((p.x-a.x)*dx+(p.z-a.z)*dz)/(dx*dx+dz*dz || 1)))
  return Math.hypot(p.x-a.x-dx*t,p.z-a.z-dz*t)
}

export function roadDistance(p: GroundPoint, roads: WorldRoad[]) {
  let nearest = Infinity
  for (const road of roads) for (let i=1;i<road.points.length;i++) nearest=Math.min(nearest,segmentDistance(p,road.points[i-1],road.points[i]))
  return nearest
}

export function civilizationOccupies(plan: CivilizationPlan, p: GroundPoint) {
  return plan.places.some((place)=>distance(p,place.center)<place.radius+0.2)
    || plan.farms.some((farm)=>Math.abs(p.x-farm.center.x)<farm.width/2+0.18 && Math.abs(p.z-farm.center.z)<farm.depth/2+0.18)
    || roadDistance(p,plan.roads)<0.29
}

export function footprint(sample: SurfaceSampler, p: GroundPoint, width: number, depth=width, maxRise=0.24) {
  const points: GroundSample[]=[]
  for(let x=-1;x<=1;x++) for(let z=-1;z<=1;z++) {
    const s=sample(p.x+x*width/2,p.z+z*depth/2)
    if(!s || s.height<WATER_LEVEL+0.07 || s.shore<0.28 || s.wetland>0.6) return null
    points.push(s)
  }
  return Math.max(...points.map((s)=>s.height))-Math.min(...points.map((s)=>s.height))<maxRise ? points : null
}

export function createCivilizationPlan(field: TerrainField, sample: SurfaceSampler): CivilizationPlan {
  const random=seededRandom(field.seed^0x774acc)
  const graph=createGraph<GroundSample,{cost:number;bridge:boolean}>()
  const nodes: GroundSample[]=[]
  // A fine graph follows the rendered ground. Only the explicit bridge may cross water.
  for(let x=-16;x<=16;x+=0.5) for(let z=-14;z<=14;z+=0.5) {
    const s=sample(x,z)
    if(s && s.height>WATER_LEVEL+0.06 && s.rock<0.55 && s.shore>0.36 && s.wetland<0.6) {
      nodes.push(s); graph.addNode(key(s),s)
    }
  }
  for(const a of nodes) for(const [dx,dz] of [[0.5,0],[0,0.5],[0.5,0.5],[-0.5,0.5]]) {
    const b=graph.getNode(key({x:a.x+dx,z:a.z+dz}))?.data
    if(!b || Math.abs(a.height-b.height)/distance(a,b)>0.42) continue
    let safe=true
    for(const t of [0.25,0.5,0.75]) {
      const s=sample(a.x+(b.x-a.x)*t,a.z+(b.z-a.z)*t)
      if(!s || s.height<WATER_LEVEL+0.06 || s.shore<0.32) safe=false
    }
    if(safe) graph.addLink(key(a),key(b),{cost:distance(a,b)*(1+(a.forest+b.forest)*0.35)+Math.abs(a.height-b.height)*7,bridge:false})
  }
  const bridgeZ=1.5
  const bank=(side:number)=>nodes.filter((p)=>p.z===bridgeZ && (p.x-field.riverX(bridgeZ))*side>0 && p.shore>0.65)
    .sort((a,b)=>Math.abs(a.x-field.riverX(bridgeZ))-Math.abs(b.x-field.riverX(bridgeZ)))[0]
  const left=bank(-1),right=bank(1)
  if(left && right) graph.addLink(key(left),key(right),{cost:distance(left,right)*1.2,bridge:true})
  const finder=aStar(graph,{distance:(_a,_b,link)=>link.data.cost,heuristic:(a,b)=>distance(a.data,b.data)})
  const plan: CivilizationPlan={places:[],roads:[],buildings:[],farms:[],docks:[]}
  const anchors: {kind:PlaceKind;label:string;x:number;z:number;radius:number}[]=[
    {kind:'town',label:'河谷集镇',x:5,z:0,radius:1.95},
    {kind:'village',label:'花甸村庄',x:-4,z:2,radius:1.35},
    {kind:'farmstead',label:'南岸农庄',x:3,z:7,radius:1.25},
    {kind:'lumber',label:'林间伐木场',x:-11,z:-4,radius:1.2},
    {kind:'quarry',label:'山麓采石场',x:10,z:2,radius:1.1},
    {kind:'ruins',label:'山道遗迹',x:-5,z:-8,radius:1},
    {kind:'harbor',label:'海湾渔村',x:2,z:11,radius:1.1},
    {kind:'lookout',label:'高地哨塔',x:-1,z:-11,radius:0.65},
  ]
  for(const anchor of anchors) {
    const target={x:anchor.x+(random()-0.5)*1.2,z:anchor.z+(random()-0.5)*1.2}
    const upland=['quarry','ruins','lookout'].includes(anchor.kind)
    const candidate=nodes.filter((p)=>distance(p,target)<3.5 && footprint(sample,p,anchor.radius*2,anchor.radius*2,upland?0.85:0.24))
      .filter((p)=>plan.places.every((place)=>distance(p,place.center)>place.radius+anchor.radius+1))
      .sort((a,b)=>distance(a,target)-distance(b,target)).find((p)=>!plan.places.length || finder.find(key(p),key(plan.places[0].center)).length>0)
    if(!candidate) continue
    const place: WorldPlace={...anchor,id:anchor.kind,center:candidate}
    if(plan.places.length) {
      // Attach each site to its nearest reachable settlement, preserving one connected network.
      const parents=[...plan.places].sort((a,b)=>distance(a.center,candidate)-distance(b.center,candidate))
      const parent=parents.find((p)=>finder.find(key(candidate),key(p.center)).length>0)!
      const path=finder.find(key(candidate),key(parent.center)).reverse().map((node)=>node.data)
      let points=[path[0]]
      for(let i=1;i<path.length;i++) {
        if(graph.getLink(key(path[i-1]),key(path[i]))?.data.bridge || graph.getLink(key(path[i]),key(path[i-1]))?.data.bridge) {
          if(points.length>1) plan.roads.push({points,bridge:false,from:parent.id,to:place.id})
          plan.roads.push({points:[path[i-1],path[i]],bridge:true,from:parent.id,to:place.id})
          points=[path[i]]
        } else points.push(path[i])
      }
      if(points.length>1) plan.roads.push({points,bridge:false,from:parent.id,to:place.id})
    }
    plan.places.push(place)
  }
  const harbor=plan.places.find((p)=>p.kind==='harbor')
  if(harbor) {
    const bank=nodes.filter((p)=>p.shore>0.36 && p.shore<0.85 && p.z>8 && distance(p,harbor.center)<5)
      .sort((a,b)=>distance(a,harbor.center)-distance(b,harbor.center)).find((p)=>finder.find(key(p),key(harbor.center)).length>0)
    if(bank) {
      const end=Array.from({length:24},(_,i)=>sample(bank.x+Math.cos(i*Math.PI/12)*1.3,bank.z+Math.sin(i*Math.PI/12)*1.3))
        .filter((p):p is GroundSample=>!!p && p.height<WATER_LEVEL-0.2).sort((a,b)=>a.height-b.height)[0]
      if(end) {
        plan.docks.push({bank,end})
        plan.roads.push({points:finder.find(key(bank),key(harbor.center)).reverse().map((n)=>n.data),bridge:false,from:harbor.id,to:'dock'})
      }
    }
  }
  for(const place of plan.places) {
    const town=place.kind==='town', rural=place.kind==='village'||place.kind==='farmstead'
    const count=town?14:rural?6:5
    let placed=0
    for(let i=0;i<count;i++) {
      const angle=i/count*Math.PI*2+(random()-0.5)*0.15
      const radius=place.radius*(town && i%2===0?0.52:0.8)
      const p={x:place.center.x+Math.sin(angle)*radius,z:place.center.z+Math.cos(angle)*radius}
      const size=town?0.72:rural?0.68:0.7
      if(roadDistance(p,plan.roads)<size*0.42+0.19) continue
      const ground=footprint(sample,p,size*0.8)
      if(!ground) continue
      const center={...sample(p.x,p.z)!,height:Math.max(...ground.map((s)=>s.height))}
      let kind:WorldBuilding['kind']='house'
      if(place.kind==='lookout') kind='tower'
      else if(place.kind==='ruins') kind='ruin'
      else if(place.kind==='lumber' && i>1) kind='logs'
      else if(place.kind==='quarry') kind=i===0?'tower':'ruin'
      else if(town && placed===0) kind='hall'
      else if(rural && placed===0) kind='mill'
      else if(rural && i===3) kind='barn'
      plan.buildings.push({placeId:place.id,center,rotation:angle+Math.PI,size,kind,variant:Math.floor(random()*4)})
      placed++
      if(place.kind==='lookout') break
    }
    if(!town && !rural) continue
    for(const [dx,dz] of [[-1,0],[1,0],[-0.6,1],[0.6,1],[0,-1]]) {
      const center=sample(place.center.x+dx*(place.radius+1.05),place.center.z+dz*(place.radius+1.4))
      if(!center || !footprint(sample,center,1.4,1.6) || center.desert>0.3 || center.badlands>0.3) continue
      const corners=[[-0.7,-0.8],[-0.7,0.8],[0.7,-0.8],[0.7,0.8]].map(([x,z])=>({x:center.x+x,z:center.z+z}))
      if([center,...corners].some((p)=>roadDistance(p,plan.roads)<0.42 || plan.places.some((s)=>distance(p,s.center)<s.radius+0.1))) continue
      if(plan.farms.some((f)=>distance(f.center,center)<1.8)) continue
      plan.farms.push({center,width:1.4,depth:1.6,crop:plan.farms.length%3})
    }
  }
  for(const road of plan.roads) {
    if(road.bridge || road.points.length<3) continue
    const curve=new CatmullRomCurve3(road.points.map((p)=>new Vector3(p.x,0,p.z)),false,'centripetal')
    const points=curve.getSpacedPoints(Math.ceil(curve.getLength()/0.12)).map((p)=>sample(p.x,p.z))
    const valid=points.every((p):p is GroundSample=>!!p && p.height>WATER_LEVEL+0.06 && p.shore>0.3)
    if(!valid) continue
    const clear=points.every((p,i)=> {
      if(i===0) return true
      const a=points[i-1],length=distance(a,p)
      return Math.abs(a.height-p.height)/length<=0.42
        && plan.buildings.every((b)=>segmentDistance(b.center,a,p)>b.size*0.42+0.19)
        && plan.farms.every((farm)=>Math.abs(p.x-farm.center.x)>farm.width/2+0.18 || Math.abs(p.z-farm.center.z)>farm.depth/2+0.18)
    })
    if(clear) road.points=points
  }
  return plan
}
