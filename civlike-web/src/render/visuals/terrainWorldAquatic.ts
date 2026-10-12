import * as THREE from 'three'
import { WATER_LEVEL, randomTilePoint, seededRandom, type GroundPoint, type GroundSample, type WorldTile } from './terrainWorld'

type Sampler = (x: number, z: number) => GroundSample | null
export type FishSchool = { center: GroundPoint; radius: number; angle: number; speed: number }
export type WorldFish = { school: FishSchool; phase: number; radius: number; size: number; color: string }

export function createAquaticPlan(seed: number, tiles: WorldTile[], sample: Sampler): WorldFish[] {
  const random=seededRandom(seed^0x2c51fa93), schools: FishSchool[]=[], fish: WorldFish[]=[]
  const candidates=tiles.filter((tile)=>(sample(tile.center.x,tile.center.z)?.height??1)<-0.2)
  const inland=candidates.filter((tile)=>Math.hypot(tile.center.x,tile.center.z)<9)
  for(let attempt=0;attempt<400 && schools.length<9 && candidates.length;attempt++) {
    const pool=attempt<180 && schools.length<4 && inland.length?inland:candidates
    const center=randomTilePoint(pool[Math.floor(random()*pool.length)],random)
    const radius=0.45+random()*0.38
    if(schools.some((school)=>Math.hypot(school.center.x-center.x,school.center.z-center.z)<2.1)) continue
    // Validate the whole school footprint, including fish bodies, against the rendered bed.
    let valid=true
    for(let r=0;r<=radius+0.16 && valid;r+=0.075) for(let i=0;i<96;i++) {
      const p=sample(center.x+Math.cos(i*Math.PI/48)*r,center.z+Math.sin(i*Math.PI/48)*r)
      if(!p || p.height>WATER_LEVEL-0.29) {valid=false;break}
    }
    if(!valid) continue
    const school={center,radius,angle:random()*Math.PI*2,speed:0.14+random()*0.1}
    schools.push(school)
    const count=5+Math.floor(random()*4), color=['#d7d7b6','#f1ac62','#426a70'][schools.length%3]
    for(let i=0;i<count;i++) fish.push({school,phase:i*0.25+random()*0.12,radius:0.55+random()*0.4,size:0.75+random()*0.4,color})
  }
  // Put an inland/river school first so the focus view includes a bank, not the map cutaway.
  const focusScore=({school:{center}}:WorldFish)=>Math.hypot(center.x,center.z)*0.15+Math.abs((sample(center.x,center.z)?.shore??-99)+0.45)
  return fish.sort((a,b)=>focusScore(a)-focusScore(b))
}

export function sampleFishMotion(fish: WorldFish, time: number, sample: Sampler, waterHeight:(x:number,z:number)=>number=()=>WATER_LEVEL+0.006) {
  const {school}=fish, a=time*school.speed+fish.phase
  const u=Math.cos(a)*school.radius*fish.radius, v=Math.sin(a)*school.radius*fish.radius*0.58
  const c=Math.cos(school.angle),s=Math.sin(school.angle)
  const x=school.center.x+u*c-v*s,z=school.center.z+u*s+v*c
  const du=-Math.sin(a),dv=Math.cos(a)*0.58
  const bed=sample(x,z)?.height??WATER_LEVEL
  const swimmingHeight=Math.min(WATER_LEVEL-0.16,bed+(WATER_LEVEL-bed)*0.62)+Math.sin(a*2+fish.phase)*0.012
  const height=Math.max(bed+0.04,Math.min(swimmingHeight,waterHeight(x,z)-0.055))
  return {x,z,height,yaw:Math.atan2(du*c-dv*s,du*s+dv*c),tail:Math.sin(time*9+fish.phase*5)*0.4}
}

export function createWorldAquatic(seed: number, tiles: WorldTile[], sample: Sampler, waterHeight?:(x:number,z:number)=>number) {
  const fish=createAquaticPlan(seed,tiles,sample),group=new THREE.Group()
  group.name='underwater-fish-schools'
  const material=new THREE.MeshStandardMaterial({roughness:0.72,flatShading:true})
  const body=new THREE.InstancedMesh(new THREE.SphereGeometry(1,8,5).scale(0.025,0.021,0.069),material,fish.length)
  const tailGeometry=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute([
    0,0,-0.055, -0.037,0,-0.114, 0,0.008,-0.092,
    0,0,-0.055, 0,0.008,-0.092, 0.037,0,-0.114,
  ],3));tailGeometry.translate(0,0,0.055);tailGeometry.computeVertexNormals()
  const finMaterial=new THREE.MeshStandardMaterial({roughness:0.85,flatShading:true,side:THREE.DoubleSide})
  const tails=new THREE.InstancedMesh(tailGeometry,finMaterial,fish.length)
  const eyes=new THREE.InstancedMesh(new THREE.SphereGeometry(0.006,5,4),new THREE.MeshBasicMaterial({color:'#192f35'}),fish.length*2)
  const transform=new THREE.Object3D(),eye=new THREE.Object3D(),tailPivot=new THREE.Object3D(),matrix=new THREE.Matrix4()
  tailPivot.position.z=-0.055
  for(const mesh of [body,tails,eyes]) {mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);mesh.frustumCulled=false;group.add(mesh)}
  fish.forEach((item,i)=>{body.setColorAt(i,new THREE.Color(item.color));tails.setColorAt(i,new THREE.Color(item.color).multiplyScalar(0.76))})
  function animate(time: number) {
    fish.forEach((item,i)=>{
      const p=sampleFishMotion(item,time,sample,waterHeight)
      transform.position.set(p.x,p.height,p.z);transform.rotation.set(0,p.yaw,Math.sin(time*4+i)*0.06);transform.scale.setScalar(item.size)
      transform.updateMatrix();body.setMatrixAt(i,transform.matrix)
      for(const side of [-1,1]) {
        eye.position.set(side*0.019,0.009,0.04);eye.updateMatrix()
        matrix.multiplyMatrices(transform.matrix,eye.matrix);eyes.setMatrixAt(i*2+(side===1?1:0),matrix)
      }
      tailPivot.rotation.y=p.tail;tailPivot.updateMatrix()
      matrix.multiplyMatrices(transform.matrix,tailPivot.matrix);tails.setMatrixAt(i,matrix)
    })
    for(const mesh of [body,tails,eyes]) mesh.instanceMatrix.needsUpdate=true
  }
  animate(0)
  return {group,fish,animate,position:(time: number)=>fish.length?sampleFishMotion(fish[0],time,sample,waterHeight):null}
}
