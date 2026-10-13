import * as THREE from 'three'
import type { WaterSurface } from './terrainWorldWater'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import { snowCover, type TerrainSeason } from './terrainWorldClimate'
import { type GroundSample } from './terrainWorld'
import { roadDistance, type CivilizationPlan, type SurfaceSampler } from './terrainWorldCivilization'
import { createBroadleafGeometry } from './terrainWorldModels'

type Finish = 'wall' | 'roof' | 'wood' | 'stone' | 'road' | 'crop' | 'soil' | 'orchard' | 'fruit'
type Piece = { geometry: THREE.BufferGeometry; color: THREE.Color; sample: GroundSample; finish: Finish }

export function createWorldScenery(plan: CivilizationPlan, sample: SurfaceSampler) {
  const group=new THREE.Group()
  group.name='settlements-and-roads'
  const pieces: Piece[]=[]
  const rotors: THREE.Group[]=[]
  const boats: THREE.Group[]=[]
  let frame=new THREE.Matrix4()
  const transform=new THREE.Object3D()
  const wood='#705944', stone='#9a9a8c'
  function add(geometry: THREE.BufferGeometry, color: string, finish: Finish) {
    geometry.applyMatrix4(frame)
    geometry.computeBoundingBox()
    const center=geometry.boundingBox!.getCenter(new THREE.Vector3())
    const ground=sample(center.x,center.z)??plan.places[0].center
    pieces.push({geometry,color:new THREE.Color(color),sample:ground,finish})
  }
  function box(x:number,y:number,z:number,w:number,h:number,d:number,color:string,finish:Finish='wood') {
    add(new THREE.BoxGeometry(w,h,d).translate(x,y,z),color,finish)
  }
  function cylinder(x:number,y:number,z:number,top:number,bottom:number,h:number,color:string,finish:Finish='stone',sides=8) {
    add(new THREE.CylinderGeometry(top,bottom,h,sides).translate(x,y,z),color,finish)
  }
  function roof(x:number,y:number,z:number,w:number,h:number,d:number,color:string) {
    const shape=new THREE.Shape().moveTo(-w/2,0).lineTo(w/2,0).lineTo(0,h).closePath()
    const geo=new THREE.ExtrudeGeometry(shape,{depth:d,bevelEnabled:false,steps:1})
    add(geo.translate(x,y,z-d/2),color,'roof')
    // Raised courses and a ridge cap keep small rooftops legible in close views.
    const trim=new THREE.Color(color).multiplyScalar(0.78).getStyle()
    box(x,y+h+0.008,z,0.035,0.025,d+0.025,trim,'roof')
    for(const side of [-1,1]) for(let course=1;course<=3;course++) {
      const px=x+side*w*course/8,py=y+h*(1-course/4)+0.009
      box(px,py,z,0.023,0.018,d+0.015,trim,'roof')
    }
  }
  function setFrame(x:number,y:number,z:number,angle=0,size=1) {
    transform.position.set(x,y,z);transform.rotation.set(0,angle,0);transform.scale.setScalar(size);transform.updateMatrix();frame=transform.matrix.clone()
  }
  function fence(x:number,z:number,length:number,alongX:boolean) {
    const count=Math.ceil(length/0.3)
    for(let i=0;i<=count;i++) {
      const px=x+(alongX?length*i/count:0),pz=z+(alongX?0:length*i/count)
      const y=sample(px,pz)?.height??0.3
      box(px,y+0.05,pz,0.018,0.1,0.018,wood)
      if(i<count) {
        const nx=x+(alongX?length*(i+1)/count:0),nz=z+(alongX?0:length*(i+1)/count)
        for(const h of [0.035,0.075]) box((px+nx)/2,y+h,(pz+nz)/2,alongX?length/count:0.012,0.012,alongX?0.012:length/count,wood)
      }
    }
  }
  // Roads and fields are tessellated against the same surface as the ground mesh.
  function patch(x:number,z:number,w:number,d:number,color:string,finish:Finish,raise=0.025) {
    const positions:number[]=[]
    const nx=Math.ceil(w/0.1),nz=Math.ceil(d/0.1)
    for(let i=0;i<nx;i++) for(let j=0;j<nz;j++) {
      const a=[x-w/2+w*i/nx,z-d/2+d*j/nz],b=[a[0]+w/nx,a[1]],c=[a[0],a[1]+d/nz],e=[b[0],c[1]]
      for(const p of [a,c,b,b,c,e]) positions.push(p[0],(sample(p[0],p[1])?.height??0.3)+raise,p[1])
    }
    const geometry=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(positions,3))
    geometry.computeVertexNormals();add(geometry,color,finish)
  }
  for(const road of plan.roads) {
    if(road.bridge) {
      const [a,b]=road.points,length=Math.hypot(b.x-a.x,b.z-a.z),count=Math.ceil(length/0.105)
      const bridgeY=(t:number)=>a.height*(1-t)+b.height*t+0.035+Math.sin(t*Math.PI)*0.22
      for(let i=0;i<=count;i++) {
        const t=i/count,x=a.x+(b.x-a.x)*t,z=a.z+(b.z-a.z)*t,y=bridgeY(t)
        box(x,y-0.035,z,length/count*0.95,0.07,0.29,i%3===0?'#ab8b61':'#967650')
        if(i%4===0 && i>0 && i<count) for(const side of [-1,1]) {
          box(x,y+0.065,z+side*0.16,0.022,0.16,0.022,wood)
          const ground=sample(x,z)?.height??-0.46
          if(i%8===0) cylinder(x,(ground+y)/2,z+side*0.2,0.065,0.09,y-ground,stone)
        }
        if(i<count) for(const side of [-1,1]) {
          const nextY=bridgeY((i+1)/count)
          const rail=new THREE.BoxGeometry(Math.hypot(length/count,nextY-y),0.035,0.035)
          rail.rotateZ(Math.atan2(nextY-y,(b.x-a.x)/count)).translate(x+(b.x-a.x)/count/2,(y+nextY)/2+0.13,z+side*0.16)
          add(rail,wood,'wood')
        }
      }
      continue
    }
    for(let i=1;i<road.points.length;i++) {
      const a=road.points[i-1],b=road.points[i],length=Math.hypot(b.x-a.x,b.z-a.z)
      const dx=(b.x-a.x)/length,dz=(b.z-a.z)/length,positions:number[]=[]
      const steps=Math.ceil(length/0.1),width=0.21
      for(let j=0;j<steps;j++) {
        const point=(t:number,side:number)=> {
          const x=a.x+dx*t-dz*side,z=a.z+dz*t+dx*side
          return [x,(sample(x,z)?.height??a.height)+0.031,z]
        }
        const p=point(j*length/steps,-width/2),q=point(j*length/steps,width/2),r=point((j+1)*length/steps,-width/2),s=point((j+1)*length/steps,width/2)
        for(const v of [p,q,r,r,q,s]) positions.push(...v)
      }
      const geo=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geo.computeVertexNormals()
      add(geo,'#c3ab79','road')
    }
  }
  for(const place of plan.places) {
    if(place.kind==='quarry') {
      const {x,z}=place.center
      for(let tier=0;tier<3;tier++) {
        const pz=z-0.48-tier*0.16,y=sample(x,pz)!.height
        box(x,y+0.12+tier*0.1,pz,1.25-tier*0.22,0.24+tier*0.2,0.31,tier%2?stone:'#bbb8a8','stone')
      }
      const y=sample(x+0.55,z+0.28)!.height
      box(x+0.55,y+0.48,z+0.28,0.09,0.96,0.09,wood)
      box(x+0.26,y+0.96,z+0.28,0.7,0.07,0.07,wood)
      box(x-0.04,y+0.68,z+0.28,0.018,0.52,0.018,wood)
      box(x-0.04,y+0.38,z+0.28,0.25,0.21,0.26,stone,'stone')
      continue
    }
    if(place.kind==='ruins' || place.kind==='lookout') continue
    const {x,z}=place.center
    patch(x,z,0.43,0.43,'#b5ae90','road')
    // A small well and courtyard read as a complete village at tile scale.
    const well=[[-0.2,0.12],[0.2,0.12],[0,-0.22]].map(([dx,dz])=>({x:x+dx,z:z+dz})).find((p)=>roadDistance(p,plan.roads)>0.19)
    if(well) {
      const y=sample(well.x,well.z)!.height
      cylinder(well.x,y+0.055,well.z,0.066,0.073,0.11,stone)
      cylinder(well.x,y+0.112,well.z,0.043,0.043,0.006,'#426b70')
    }
    if(['town','village','farmstead'].includes(place.kind)) for(let edge=0;edge<6;edge++) {
      const a=(edge/3+1/6)*Math.PI,b=a+Math.PI/3
      const start={x:x+Math.cos(a)*1.035,z:z+Math.sin(a)*1.035},end={x:x+Math.cos(b)*1.035,z:z+Math.sin(b)*1.035}
      for(let j=0;j<6;j++) {
        const px=start.x+(end.x-start.x)*(j+0.5)/6,pz=start.z+(end.z-start.z)*(j+0.5)/6
        if(roadDistance({x:px,z:pz},plan.roads)<0.24) continue
        const y=sample(px,pz)?.height
        if(y===undefined) continue
        setFrame(px,y,pz,-Math.atan2(end.z-start.z,end.x-start.x))
        if(place.kind==='town') box(0,0.055,0,0.178,0.11,0.045,stone,'stone')
        else for(const h of [0.035,0.075]) box(0,h,0,0.174,0.012,0.015,wood)
        box(-0.086,0.07,0,0.025,0.14,0.025,place.kind==='town'?stone:wood,place.kind==='town'?'stone':'wood')
        frame.identity()
      }
    }
    if(place.kind==='town') {
      for(const dx of [-0.675,-0.405,-0.135,0.135,0.405,0.675]) patch(x+dx,z,0.035,1.3,'#c5b99a','road')
      for(const dz of [-0.405,0.405,0.675]) patch(x,z+dz,1.3,0.035,'#c5b99a','road')
      // The market stands flank a central street, rather than blocking it.
      for(const side of [-1,1]) {
        const px=x+side*0.23,pz=z-0.05,y=sample(px,pz)!.height
        if(roadDistance({x:px,z:pz},plan.roads)<0.19 || (well && Math.hypot(px-well.x,pz-well.z)<0.17)) continue
        box(px,y+0.045,pz,0.12,0.065,0.09,wood)
        box(px,y+0.16,pz,0.145,0.015,0.12,side<0?'#a45244':'#488781','roof')
        for(const dx of [-0.06,0.06]) box(px+dx,y+0.09,pz,0.009,0.16,0.009,wood)
        for(let j=0;j<3;j++) box(px-0.04+j*0.04,y+0.084,pz,0.026,0.02,0.06,'#d0ad59','crop')
      }
    }
  }
  for(const b of plan.buildings) {
    setFrame(b.center.x,b.center.height-0.015,b.center.z,b.kind==='mill'?0.18:b.rotation,b.size)
    const roofColor=['#ad6650','#4b7d80','#857d69','#854c50'][b.variant]
    const wall=['#e4d9b9','#dad7c5','#d4bb8e','#e2c7ae'][b.variant]
    if(b.kind==='ruin') {
      for(let j=0;j<3;j++) {
        box(-0.26+j*0.25,0.11+j%2*0.09,0,0.22,0.22+j%2*0.18,0.32,stone,'stone')
        box(-0.26+j*0.25,0.07,0.35,0.22,0.14,0.24,'#b6b3a2','stone')
      }
      if(b.variant%2===0) { box(-0.25,0.4,0,0.15,0.7,0.18,stone,'stone');box(0.25,0.35,0,0.15,0.6,0.18,stone,'stone');box(0,0.69,0,0.67,0.14,0.22,stone,'stone') }
      continue
    }
    if(b.kind==='logs') {
      for(let j=0;j<5;j++) {
        const geo=new THREE.CylinderGeometry(0.08,0.08,0.8,7).rotateZ(Math.PI/2).translate(0,0.09+(j>2?0.14:0),-0.18+(j%3)*0.17)
        add(geo,j%2?wood:'#92714c','wood')
      }
      continue
    }
    const tower=b.kind==='hall'||b.kind==='tower'||b.kind==='mill',h=tower?1.2:0.55
    const w=b.kind==='barn'?0.95:0.68,d=b.kind==='barn'?0.82:0.64
    box(0,-0.06,0,w+0.1,0.35,d+0.1,stone,'stone')
    if(b.kind==='mill') cylinder(0,h/2,0,0.22,0.39,h,wall,'wall')
    else box(0,h/2+0.08,0,w,h,d,wall,'wall')
    roof(0,h+0.08,0,w+0.18,0.33,d+0.18,roofColor)
    for(const side of [-1,1]) {
      box(side*w/2,h/2+0.08,d/2+0.012,0.035,h,0.035,wood)
      box(side*0.2,h*0.62,d/2+0.015,0.12,0.15,0.025,'#334e52')
      box(side*0.2,h*0.62,d/2+0.03,0.012,0.15,0.025,wall,'wall')
      box(side*0.2,h*0.62-0.085,d/2+0.036,0.17,0.025,0.06,wood)
      for(const shutter of [-1,1]) box(side*0.2+shutter*0.08,h*0.62,d/2+0.033,0.028,0.17,0.02,roofColor,'wood')
    }
    box(0,0.23,d/2+0.02,0.15,0.31,0.03,wood)
    box(0,0.035,d/2+0.065,0.21,0.04,0.10,stone,'stone')
    box(0,0.405,d/2+0.035,0.20,0.028,0.035,wood)
    box(0.045,0.23,d/2+0.041,0.014,0.025,0.014,'#c5ae72','wood')
    box(0,h*0.42,d/2+0.014,w,0.035,0.025,wood)
    box(0.19,h+0.23,-0.14,0.13,0.35,0.13,stone,'stone')
    box(0.19,h+0.405,-0.14,0.16,0.035,0.16,'#b7ad97','stone')
    box(0.19,h+0.425,-0.14,0.08,0.006,0.08,'#454444','stone')
    for(const side of [-1,1]) {
      box(side*(w/2+0.012),h*0.62,0,0.025,0.16,0.14,'#334e52')
      box(side*(w/2+0.03),h*0.62,0,0.012,0.16,0.015,wall,'wall')
      box(0,h*0.62,-d/2-0.012,0.14,0.16,0.025,'#334e52')
    }
    if(b.kind==='hall') {
      cylinder(0,h+0.7,0,0.012,0.018,0.58,wood,'wood',5)
      box(0.12,h+0.89,0,0.24,0.16,0.025,'#d2a548','roof')
    }
    if(b.kind==='mill') {
      const rotor=new THREE.Group()
      rotor.position.set(0,h*0.9,d/2+0.18)
      const rotorMaterial=new THREE.MeshStandardMaterial({color:'#eee4c8',roughness:1,flatShading:true})
      for(let j=0;j<4;j++) {
        const arm=new THREE.Group();arm.rotation.z=j*Math.PI/2
        const beam=new THREE.Mesh(new THREE.BoxGeometry(0.04,0.8,0.035).translate(0,0.37,0),rotorMaterial)
        const sail=new THREE.Mesh(new THREE.BoxGeometry(0.2,0.45,0.024).translate(0.07,0.51,0.025),rotorMaterial)
        arm.add(beam,sail);rotor.add(arm)
      }
      const base=new THREE.Group();base.applyMatrix4(frame);base.add(rotor);group.add(base);rotors.push(rotor)
    }
  }
  frame.identity()
  for(const dock of plan.docks) {
    const {bank,end}=dock,length=Math.hypot(end.x-bank.x,end.z-bank.z),angle=Math.atan2(end.x-bank.x,end.z-bank.z)
    const deck=bank.height+0.09
    setFrame(bank.x,deck,bank.z,angle)
    for(let i=0;i<=12;i++) {
      box(0,0,i*length/12,0.3,0.045,length/12*0.94,'#a98c62')
      if(i%4===0) for(const side of [-1,1]) {
        cylinder(side*0.17,-0.22,i*length/12,0.025,0.035,0.64,wood,'wood',6)
      }
    }
    const boat=new THREE.Group()
    boat.name='moored-boat'
    const hull=new THREE.Mesh(new THREE.CylinderGeometry(0.23,0.14,0.15,6),new THREE.MeshStandardMaterial({color:wood,roughness:1,flatShading:true}))
    hull.scale.set(0.8,1,2.4);boat.add(hull)
    const mast=new THREE.Mesh(new THREE.CylinderGeometry(0.012,0.02,0.66,5).translate(0,0.34,0),new THREE.MeshStandardMaterial({color:wood,roughness:1}));boat.add(mast)
    const sailGeo=new THREE.BufferGeometry().setAttribute('position',new THREE.Float32BufferAttribute([0,0.66,0,0,0.2,-0.36,0,0.2,0.23],3));sailGeo.computeVertexNormals()
    boat.add(new THREE.Mesh(sailGeo,new THREE.MeshStandardMaterial({color:'#ede1bc',side:THREE.DoubleSide,roughness:1})))
    // The boat is moored alongside the pier in open water, not on its approach.
    const bx=end.x+Math.cos(angle)*0.62,bz=end.z-Math.sin(angle)*0.62
    if((sample(bx,bz)?.height??1)<0.04) {
      boat.position.set(bx,0.12,bz);boat.rotation.y=angle;boat.scale.setScalar(0.55);group.add(boat);boats.push(boat)
    } else { hull.geometry.dispose();hull.material.dispose();mast.geometry.dispose();mast.material.dispose();sailGeo.dispose();(boat.children[2] as THREE.Mesh<THREE.BufferGeometry,THREE.Material>).material.dispose() }
    frame.identity()
  }
  for(const farm of plan.farms) {
    const {x,z}=farm.center
    patch(x,z,farm.width,farm.depth,'#8f7451','soil',0.029)
    if(farm.crop===2) {
      for(let row=0;row<2;row++) for(let j=0;j<3;j++) {
        const px=x-farm.width*0.27+row*farm.width*0.54,pz=z-farm.depth*0.32+j*farm.depth*0.32,y=sample(px,pz)!.height
        cylinder(px,y+0.12,pz,0.012,0.023,0.24,wood,'wood',5)
        const canopy=createBroadleafGeometry((row+j)%4).scale(0.19,0.19,0.19).translate(px,y+0.12,pz)
        canopy.deleteAttribute('color')
        add(canopy,'#729849','orchard')
        for(const side of [-1,1]) add(new THREE.IcosahedronGeometry(0.02,0).translate(px+side*0.11,y+0.25,pz+0.06),'#bd6748','fruit')
      }
    } else {
    for(let row=0;row<6;row++) {
      const px=x-farm.width/2+farm.width*(row+0.5)/6
      patch(px,z,0.075,farm.depth-0.15,['#bfc16c','#759555','#caaa54'][farm.crop],'crop',0.035)
      for(let j=0;j<10;j++) {
        if(farm.crop===0 && row>=4 && j>=8) continue
        const pz=z-farm.depth/2+farm.depth*(j+0.5)/10,y=sample(px,pz)!.height
        if(farm.crop===0) {
          box(px,y+0.065,pz,0.012,0.07,0.012,'#b9b16a','crop')
          add(new THREE.ConeGeometry(0.023,0.055,4).translate(px,y+0.115,pz),'#d6be68','crop')
        } else if(j%2===0) {
          add(new THREE.IcosahedronGeometry(0.065,0).scale(1,0.65,1).translate(px,y+0.065,pz),'#7d9e62','crop')
        }
      }
    }
    }
    if(farm.crop===0) for(let bundle=0;bundle<3;bundle++) {
      const px=x+0.33+bundle*0.11,pz=z+farm.depth*0.35,y=sample(px,pz)!.height
      cylinder(px,y+0.075,pz,0.026,0.054,0.15,'#c7ad64','crop',6)
      cylinder(px,y+0.07,pz,0.034,0.034,0.016,wood,'wood',6)
    }
    fence(x-farm.width/2-0.04,z-farm.depth/2-0.04,farm.width+0.08,true)
    fence(x-farm.width/2-0.04,z-farm.depth/2-0.04,farm.depth+0.08,false)
    // Leave a farm gate in the opposite edge; complete the enclosure around it.
    fence(x+farm.width/2+0.04,z-farm.depth/2-0.04,farm.depth+0.08,false)
    const span=(farm.width-0.22)/2
    fence(x-farm.width/2-0.04,z+farm.depth/2+0.04,span,true)
    fence(x+0.15,z+farm.depth/2+0.04,span,true)
  }
  const seasonal: ((season:TerrainSeason)=>void)[]=[]
  for(const finish of ['wall','roof','wood','stone','road','crop','soil','orchard','fruit'] as Finish[]) {
    const list=pieces.filter((piece)=>piece.finish===finish)
    if(!list.length) continue
    for(const item of list) {
      if(item.geometry.index) { const expanded=item.geometry.toNonIndexed();item.geometry.dispose();item.geometry=expanded }
      item.geometry.deleteAttribute('uv')
    }
    const geometry=mergeGeometries(list.map((p)=>p.geometry))!
    const colors=new THREE.Float32BufferAttribute(new Float32Array(geometry.getAttribute('position').count*3),3)
    geometry.setAttribute('color',colors)
    const mat=new THREE.MeshStandardMaterial({vertexColors:true,roughness:1,flatShading:true,side:THREE.DoubleSide})
    const mesh=new THREE.Mesh(geometry,mat);mesh.castShadow=finish!=='road'&&finish!=='soil';mesh.receiveShadow=true;group.add(mesh)
    const ranges=list.map((p)=>({count:p.geometry.getAttribute('position').count,color:p.color,sample:p.sample}))
    list.forEach((p)=>p.geometry.dispose())
    seasonal.push((season)=> {
      if(finish==='orchard') mesh.visible=season.foliage>0.05
      if(finish==='fruit') mesh.visible=['green','dry','harvest'].includes(season.id)
      let offset=0
      for(const part of ranges) {
        const base=part.color.clone(),snow=snowCover(part.sample,season)
        if(finish==='crop') base.lerp(new THREE.Color(season.litter>0.5?'#957e50':season.dry>0.3?'#d9bc59':'#87a95b'),0.8)
        if(finish==='orchard') base.lerp(new THREE.Color(season.leaves[0]),0.6)
        for(let i=0;i<part.count;i++) {
          const up=geometry.getAttribute('normal').getY(offset+i)
          const color=base.clone().lerp(new THREE.Color('#e6efec'),snow*Math.max(0,up)*(finish==='wood'?0.35:0.94))
          colors.setXYZ(offset+i,color.r,color.g,color.b)
        }
        offset+=part.count
      }
      colors.needsUpdate=true
    })
  }
  let freeze=0
  return {group,updateSeason:(season:TerrainSeason)=>{freeze=season.ice;seasonal.forEach((update)=>update(season))},animate:(time:number,waterTime=time,waterAt?:(x:number,z:number)=>WaterSurface)=> {
    rotors.forEach((rotor,i)=>{rotor.rotation.z=time*0.65+i})
    boats.forEach((boat)=>{
      if(waterAt) {
        const water=waterAt(boat.position.x,boat.position.z),a=boat.rotation.y
        boat.position.y=water.height+0.034
        boat.rotation.x=Math.atan(-water.dx*Math.sin(a)-water.dz*Math.cos(a))
        boat.rotation.z=Math.atan(water.dx*Math.cos(a)-water.dz*Math.sin(a))
      } else {boat.position.y=0.12+Math.sin(waterTime*1.6)*0.018*(1-freeze);boat.rotation.z=Math.sin(waterTime)*0.025*(1-freeze)}
    })
  },rotors:rotors.length}
}
