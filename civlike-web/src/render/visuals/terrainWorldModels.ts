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
  const parts = [
    crown(57 + variant * 13, 0.45, 1.12).rotateZ(-0.23).translate(-0.22, 0.62, 0.03),
    crown(89 + variant * 9, 0.4, 1.27).rotateZ(0.16).translate(0.19, 0.9, 0.02),
    crown(26 + variant * 19, 0.33, 0.93).rotateX(-0.24).translate(0.04, 0.73, 0.29),
  ]
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
  for (let i = 0; i < 4; i++) {
    const angle = i * 2.4, dx = Math.cos(angle), dz = Math.sin(angle)
    const h = 0.09 + i % 3 * 0.026, w = 0.013
    positions.push(-dz*w,0,dx*w, dz*w,0,-dx*w, dx*0.06,h,dz*0.06)
  }
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  geometry.computeVertexNormals()
  return paintFacets(geometry, 27)
}

export function createFlowerGeometry(): THREE.BufferGeometry {
  const parts: THREE.BufferGeometry[] = []
  for (let i = 0; i < 3; i++) {
    const flower = new THREE.CircleGeometry(0.026, 5).rotateX(-Math.PI / 2)
    parts.push(flower.toNonIndexed().translate(Math.cos(i * 2.4) * 0.055, 0.08 + i * 0.025, Math.sin(i * 2.4) * 0.055))
    flower.dispose()
  }
  return paintFacets(join(parts), 45)
}
