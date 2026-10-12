import * as THREE from 'three'
import { ConvexGeometry } from 'three/examples/jsm/geometries/ConvexGeometry.js'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import { seededRandom } from './terrainWorld'

function join(parts: THREE.BufferGeometry[]): THREE.BufferGeometry {
  const geometry = mergeGeometries(parts)
  parts.forEach((part) => part.dispose())
  return geometry
}

function paintFacets(geometry: THREE.BufferGeometry, seed: number, contrast = 0.16): THREE.BufferGeometry {
  const random = seededRandom(seed)
  const normal = geometry.getAttribute('normal')
  const colors: number[] = []
  for (let i = 0; i < normal.count; i += 3) {
    const light = 0.82 + normal.getY(i) * 0.1 + random() * contrast
    for (let j = 0; j < 3; j++) colors.push(light, light, light * 0.94)
  }
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3))
  return geometry
}

// Irregular ring hulls keep a sculpted silhouette without the repeated icosphere shape.
function crown(seed: number, width: number, height: number): THREE.BufferGeometry {
  const random = seededRandom(seed)
  const points: THREE.Vector3[] = []
  const lean = (random() - 0.5) * 0.28
  for (let ring = 0; ring < 4; ring++) {
    const radius = [0.38, 0.95, 0.79, 0.15][ring] * width
    for (let i = 0; i < 6; i++) {
      const angle = i * Math.PI / 3 + ring * 0.24
      const r = radius * (0.8 + random() * 0.32)
      points.push(new THREE.Vector3(Math.cos(angle) * r + lean * ring, (ring / 3 + random() * 0.08) * height, Math.sin(angle) * r))
    }
  }
  return new ConvexGeometry(points)
}

export function createBroadleafGeometry(variant: number): THREE.BufferGeometry {
  const random=seededRandom(variant+718),parts:THREE.BufferGeometry[]=[]
  // Oak, upright birch, spreading canopy and drooping willow silhouettes.
  const count=[7,5,6,8][variant%4]
  for(let i=0;i<count;i++) {
    const angle=i*2.399,radius=i===0?0:0.26+random()*0.12
    const width=variant===1?0.26:0.34+random()*0.12
    const height=variant===1?0.78:variant===2?0.38:0.5+random()*0.15
    const y=variant===1?0.65+i*0.2:variant===2?1.02+random()*0.12:0.72+random()*0.35
    parts.push(crown(100+i+variant*20,width,height).translate(Math.cos(angle)*radius,y,Math.sin(angle)*radius))
    if(variant===3 && i>0) parts.push(crown(300+i,0.16,0.62).translate(Math.cos(angle)*0.48,0.42,Math.sin(angle)*0.48))
  }
  return paintFacets(join(parts), variant + 10)
}

export function createPineGeometry(variant: number): THREE.BufferGeometry {
  const random = seededRandom(variant * 31 + 3)
  const parts: THREE.BufferGeometry[] = []
  for (let tier = 0; tier < 5; tier++) {
    const points: THREE.Vector3[] = []
    const radius = 0.62 - tier * 0.105
    const y = 0.47 + tier * 0.34
    const offset = Math.sin(tier * 1.1 + variant) * 0.07
    for (let i = 0; i < 7; i++) {
      const angle = i * Math.PI * 2 / 7 + tier * 0.49
      const r = radius * (0.75 + random() * 0.44)
      points.push(new THREE.Vector3(Math.cos(angle) * r + offset, y + random() * 0.17, Math.sin(angle) * r))
    }
    points.push(new THREE.Vector3(offset + 0.06, y + 0.95 - tier * 0.07, -0.04))
    points.push(new THREE.Vector3(offset, y - 0.12, 0))
    parts.push(new ConvexGeometry(points))
  }
  return paintFacets(join(parts), variant + 71, 0.23)
}

export function createShrubGeometry(variant: number): THREE.BufferGeometry {
  return paintFacets(join([
    crown(variant + 150, 0.32, 0.47).translate(-0.14, -0.04, 0),
    crown(variant + 200, 0.27, 0.56).translate(0.16, -0.02, 0.06),
  ]), variant + 211)
}

export function createBoulderGeometry(variant: number): THREE.BufferGeometry {
  const random = seededRandom(variant + 513)
  const points: THREE.Vector3[] = []
  for (let ring = 0; ring < 3; ring++) {
    for (let i = 0; i < 6; i++) {
      const angle = i * Math.PI / 3 + ring * 0.31
      const radius = [0.36, 0.49, 0.25][ring] * (0.78 + random() * 0.4)
      points.push(new THREE.Vector3(Math.cos(angle) * radius + ring * 0.045, ring * 0.25 + random() * 0.15 - 0.15, Math.sin(angle) * radius))
    }
  }
  return paintFacets(new ConvexGeometry(points), variant + 500, 0.25)
}

export function createGrassGeometry(): THREE.BufferGeometry {
  const positions: number[] = []
  for (let i = 0; i < 7; i++) {
    const angle = i * 2.4, dx = Math.cos(angle), dz = Math.sin(angle)
    const h = 0.13 + i % 3 * 0.05, w = 0.018
    const a = [-dz*w,0,dx*w], b = [dz*w,0,-dx*w]
    const c = [dx*0.038-dz*w*0.6,h*0.62,dz*0.038+dx*w*0.6]
    const d = [dx*0.038+dz*w*0.6,h*0.62,dz*0.038-dx*w*0.6]
    const tip = [dx*0.1,h,dz*0.1]
    positions.push(...a,...b,...c,...b,...d,...c,...c,...d,...tip)
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geometry.computeVertexNormals()
  return paintFacets(geometry, 27)
}

export function createFlowerGeometry(): THREE.BufferGeometry {
  const positions: number[] = [], colors: number[] = []
  const add = (points: number[], color: number[]) => { positions.push(...points); for (let i = 0; i < 3; i++) colors.push(...color) }
  for (let i = 0; i < 4; i++) {
    const x = Math.cos(i * 2.4) * 0.085, z = Math.sin(i * 2.4) * 0.085, y = 0.12 + i * 0.026
    add([x-0.006,0,z,x+0.006,0,z,x,y,z], [0.3,0.5,0.16])
    for (let petal = 0; petal < 5; petal++) {
      const a = petal * Math.PI * 2 / 5, b = a + 0.75
      add([x,y,z,x+Math.cos(a)*0.047,y+0.009,z+Math.sin(a)*0.047,x+Math.cos(b)*0.042,y+0.009,z+Math.sin(b)*0.042], [1,0.98,0.9])
    }
    add([x-0.016,y+0.012,z-0.012,x,y+0.012,z+0.019,x+0.016,y+0.012,z-0.012], [1,0.65,0.15])
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions,3))
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors,3))
  geometry.computeVertexNormals()
  return geometry
}

export function createReedGeometry(): THREE.BufferGeometry {
  const positions: number[] = []
  for (let i = 0; i < 6; i++) {
    const a = i * 2.4, x = Math.cos(a)*0.08, z = Math.sin(a)*0.08, h = 0.3+i%3*0.12
    positions.push(x-0.008,0,z,x+0.008,0,z,x+0.03,h,z+0.018,
      x,0.1,z,x+0.022,0.2,z+0.02,x+Math.cos(a)*0.19,h*0.8,z+Math.sin(a)*0.19)
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3))
  geometry.computeVertexNormals()
  return paintFacets(geometry,117)
}

export function createFernGeometry(): THREE.BufferGeometry {
  const positions: number[] = []
  for (let i = 0; i < 7; i++) {
    const a = i*2.4, dx=Math.cos(a), dz=Math.sin(a)
    for (let j=1;j<=4;j++) {
      const t=j/5, x=dx*t*0.28, z=dz*t*0.28, y=Math.sin(t*2.5)*0.19
      const w=(1-t)*0.082
      positions.push(x-dz*w,y,z+dx*w,x+dz*w,y,z-dx*w,x+dx*0.09,y+0.02,z+dz*0.09)
    }
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3))
  geometry.computeVertexNormals()
  return paintFacets(geometry,118)
}

export function createBareTreeGeometry(): THREE.BufferGeometry {
  const branch = (a: THREE.Vector3, b: THREE.Vector3, width: number) => {
    const delta = b.clone().sub(a)
    return new THREE.CylinderGeometry(width * 0.38, width, delta.length(), 5).toNonIndexed()
      .applyQuaternion(new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0,1,0), delta.clone().normalize()))
      .translate(...a.clone().add(b).multiplyScalar(0.5).toArray())
  }
  const parts = [branch(new THREE.Vector3(), new THREE.Vector3(0.04,1.8,0),0.08)]
  for (let i=0;i<8;i++) {
    const a=i*2.4, y=0.55+i*0.12
    const tip=new THREE.Vector3(Math.cos(a)*0.48,y+0.48,Math.sin(a)*0.48)
    parts.push(branch(new THREE.Vector3(0,y,0),tip,0.035))
    parts.push(branch(tip.clone().multiplyScalar(0.8),tip.clone().add(new THREE.Vector3(0.1,0.2,-0.1)),0.013))
  }
  return paintFacets(join(parts),128)
}

export function createCactusGeometry(): THREE.BufferGeometry {
  const parts = [new THREE.CylinderGeometry(0.075,0.11,0.95,7).toNonIndexed().translate(0,0.475,0)]
  for (const side of [-1,1]) {
    const y=side===1?0.37:0.55
    parts.push(new THREE.CylinderGeometry(0.065,0.075,0.25,6).toNonIndexed().rotateZ(Math.PI/2).translate(side*0.15,y,0))
    parts.push(new THREE.CylinderGeometry(0.045,0.065,0.28,6).toNonIndexed().translate(side*0.27,y+0.13,0))
  }
  return paintFacets(join(parts),131)
}

export function createLilyGeometry(): THREE.BufferGeometry {
  return paintFacets(new THREE.CircleGeometry(0.14,7,0.15,Math.PI*1.85).toNonIndexed().rotateX(-Math.PI/2),142)
}

export function createLeafLitterGeometry(): THREE.BufferGeometry {
  const positions:number[]=[]
  for(let i=0;i<6;i++) {
    const x=Math.cos(i*2.4)*0.14,z=Math.sin(i*2.4)*0.14
    positions.push(x-0.03,0.009,z,x,0.014,z+0.05,x+0.035,0.009,z,x-0.03,0.009,z,x+0.035,0.009,z,x,0.012,z-0.05)
  }
  const geometry=new THREE.BufferGeometry()
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3))
  geometry.computeVertexNormals()
  return paintFacets(geometry,144)
}
