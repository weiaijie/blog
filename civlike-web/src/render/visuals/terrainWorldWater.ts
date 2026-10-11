import * as THREE from 'three'
import { WATER_LEVEL, smoothstep, type GroundSample, type TerrainField } from './terrainWorld'

export type WaterEnvironment = { depth: number; across: number; along: number; river: number; climate: number; still: number; edge: number }
export type WaterSurface = { height: number; dx: number; dz: number }
// The same spectrum drives GPU displacement and CPU buoyancy.
const SWELLS = [[1.7, 0.85, 1.35, 0.048], [-0.95, 2.6, 1.8, 0.024], [4.1, 1.7, 2.5, 0.012]]
const glsl = (n: number) => Number.isInteger(n) ? `${n}.0` : String(n)
const waveFunction = `
  float swell(vec2 p,float t) {
    return ${SWELLS.map(([x,z,s,a])=>`${glsl(a)}*sin(dot(p,vec2(${glsl(x)},${glsl(z)}))-t*${glsl(s)})`).join('+')};
  }
  float waveHeight(vec2 p,vec3 flow,float depth,float climate,float still,float edge) {
    float riverWave=sin(flow.y*5.2-flowTime*2.8+sin(flow.x*2.2)*0.35)*0.024
      +sin(flow.y*8.4-flow.x*1.8-flowTime*3.6)*0.009;
    float amplitude=waveStrength*smoothstep(0.0,0.24,depth)*(1.0-iceAmount*climate)*(1.0-still*0.85)*edge;
    return mix(swell(p,flowTime),riverWave,flow.z)*amplitude;
  }
`

export function waterEnvironment(field: TerrainField, sample: GroundSample, edge = 1): WaterEnvironment {
  return { ...field.waterCoordinates(sample.x,sample.z), depth: Math.max(0,WATER_LEVEL-sample.height),
    climate: Math.max(0,0.65+sample.cold*0.35-sample.desert*0.6-sample.badlands*0.25), still:sample.wetland, edge }
}

export function sampleWaterHeight(x: number, z: number, time: number, env: WaterEnvironment, strength = 1, ice = 0): number {
  const ocean=SWELLS.reduce((sum,[kx,kz,speed,amplitude])=>sum+amplitude*Math.sin(x*kx+z*kz-time*speed),0)
  const river=Math.sin(env.along*5.2-time*2.8+Math.sin(env.across*2.2)*0.35)*0.024
    +Math.sin(env.along*8.4-env.across*1.8-time*3.6)*0.009
  const amplitude=strength*smoothstep(0,0.24,env.depth)*(1-ice*env.climate)*(1-env.still*0.85)*env.edge
  return WATER_LEVEL+0.006+(ocean*(1-env.river)+river*env.river)*amplitude
}

// Flow coordinates are shared in world space: cross-channel distance and river arc length.
export function createTerrainWaterMaterial(time: { value: number }): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    transparent: true, depthWrite: false,
    uniforms: { flowTime: time, waveStrength: { value: 1 }, iceAmount: { value: 0 }, deepColor: { value: new THREE.Color('#087d96') }, shallowColor: { value: new THREE.Color('#61cbbb') } },
    vertexShader: `
      attribute float waterDepth;
      attribute vec3 waterFlow;
      attribute float waterClimate;
      attribute float waterStill;
      attribute float waterEdge;
      uniform float flowTime;
      uniform float waveStrength;
      uniform float iceAmount;
      varying float vDepth;
      varying vec3 vFlow;
      varying vec3 vWorld;
      varying float vClimate;
      varying float vStill;
      varying float vWave;
      ${waveFunction}
      void main() {
        vDepth=waterDepth; vFlow=waterFlow; vWorld=position; vClimate=waterClimate; vStill=waterStill;
        vec3 p=position;
        vWave=waveHeight(p.xz,waterFlow,waterDepth,waterClimate,waterStill,waterEdge);
        p.y+=vWave; vWorld=p;
        gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);
      }`,
    fragmentShader: `
      uniform float flowTime;
      uniform float waveStrength;
      uniform float iceAmount;
      uniform vec3 deepColor;
      uniform vec3 shallowColor;
      varying float vDepth;
      varying vec3 vFlow;
      varying vec3 vWorld;
      varying float vClimate;
      varying float vStill;
      varying float vWave;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float noise2(vec2 p){
        vec2 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
      }
      void main(){
        float liquid=1.0-iceAmount*vClimate;
        vec2 ocean=vWorld.xz*2.4-vec2(flowTime*0.22,flowTime*0.36);
        vec2 river=vec2(vFlow.x*3.4,vFlow.y*2.8-flowTime*1.8);
        vec2 p=mix(ocean,river,vFlow.z);
        vec3 n=normalize(cross(dFdx(vWorld),dFdy(vWorld)));
        if(n.y<0.0) n=-n;
        n=normalize(vec3(n.x*1.6,n.y,n.z*1.6));
        float detail=sin(p.x*2.1+p.y*1.7)*cos(p.y*2.8)*0.025*liquid;
        n=normalize(n+vec3(detail,0.0,detail*0.6));
        vec3 viewDir=normalize(cameraPosition-vWorld);
        vec3 halfDir=normalize(normalize(vec3(-0.45,0.85,0.3))+viewDir);
        float glint=pow(max(0.0,dot(n,halfDir)),85.0);
        float depth=smoothstep(0.01,0.54,vDepth);
        vec3 c=mix(shallowColor,deepColor,depth);
        c=mix(c,vec3(0.12,0.31,0.25),vStill*0.7);
        c*=0.63+dot(n,normalize(vec3(-0.7,0.65,0.3)))*0.46+vWave*2.3;
        c*=mix(0.72,1.25,smoothstep(-0.035,0.035,vWave));
        float brokenWave=smoothstep(0.38,0.7,noise2(vec2(p.x*1.8,p.y*0.4)));
        float swellPhase=dot(vWorld.xz,vec2(1.7,0.85))-flowTime*1.35;
        float crest=pow(max(0.0,sin(swellPhase)),180.0)*brokenWave*0.1*(1.0-vFlow.z)*min(1.0,waveStrength);
        float streak=pow(max(0.0,sin(p.y*3.0+sin(p.x*1.7)*0.7)),28.0)*brokenWave*vFlow.z*0.17;
        float shorePhase=vDepth*28.0-flowTime*1.6+noise2(vWorld.xz*4.0)*2.0;
        float wash=pow(0.5+0.5*sin(shorePhase),12.0);
        float foam=(1.0-smoothstep(0.03,0.19,vDepth))*smoothstep(0.003,0.025,vDepth)*wash;
        foam*=0.35+0.65*noise2(vWorld.xz*12.0-vec2(flowTime*0.3));
        float caustic=(1.0-depth)*pow(1.0-abs(sin(p.x*3.7+sin(p.y*2.1))),10.0)*0.14;
        float fresnel=pow(1.0-max(0.0,dot(viewDir,n)),3.0);
        c=mix(c,vec3(0.72,0.94,0.9),(crest+foam*0.85+streak+caustic)*(1.0-vStill*0.95)*liquid);
        c+=vec3(0.025,0.035,0.03)*glint*liquid+vec3(0.06,0.08,0.1)*fresnel;
        float frozen=smoothstep(0.18,0.5,iceAmount*vClimate*(1.0-smoothstep(0.08,0.44,vDepth)*0.65));
        float crack=1.0-smoothstep(0.01,0.03,abs(noise2(vWorld.xz*5.0)-0.5));
        vec3 ice=mix(vec3(0.32,0.57,0.64),vec3(0.77,0.9,0.92),noise2(vWorld.xz*1.7)*0.65+0.35)-crack*0.1;
        c=mix(c,ice,frozen);
        float alpha=mix(0.48,0.7,depth)+fresnel*0.12;
        gl_FragColor=vec4(c,mix(alpha,1.0,frozen));
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  })
}
