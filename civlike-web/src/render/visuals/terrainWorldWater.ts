import * as THREE from 'three'

// Flow coordinates are shared in world space: cross-channel distance and river arc length.
export function createTerrainWaterMaterial(time: { value: number }): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: { flowTime: time, iceAmount: { value: 0 }, deepColor: { value: new THREE.Color('#087b99') }, shallowColor: { value: new THREE.Color('#68c7b9') } },
    vertexShader: `
      attribute float waterDepth;
      attribute vec3 waterFlow;
      attribute float waterClimate;
      attribute float waterStill;
      uniform float flowTime;
      uniform float iceAmount;
      varying float vDepth;
      varying vec3 vFlow;
      varying vec3 vWorld;
      varying float vClimate;
      varying float vStill;
      void main() {
        vDepth=waterDepth; vFlow=waterFlow; vWorld=position; vClimate=waterClimate; vStill=waterStill;
        vec3 p=position;
        float wave=sin(position.x*1.9+position.z*1.2-flowTime*1.4)*0.009;
        p.y+=wave*smoothstep(0.04,0.2,waterDepth)*(1.0-iceAmount*waterClimate)*(1.0-waterStill*0.85);
        gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);
      }`,
    fragmentShader: `
      uniform float flowTime;
      uniform float iceAmount;
      uniform vec3 deepColor;
      uniform vec3 shallowColor;
      varying float vDepth;
      varying vec3 vFlow;
      varying vec3 vWorld;
      varying float vClimate;
      varying float vStill;
      float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float noise2(vec2 p){
        vec2 i=floor(p),f=fract(p); f=f*f*(3.0-2.0*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);
      }
      float waterHeight(vec2 p){
        return noise2(p)*0.65+noise2(p*2.13+vec2(3.1,1.7))*0.25+noise2(p*4.1)*0.1;
      }
      void main(){
        vec2 ocean=vWorld.xz*2.4-vec2(flowTime*0.22,flowTime*0.36);
        vec2 river=vec2(vFlow.x*3.4,vFlow.y*2.8-flowTime*1.8);
        float oceanH=waterHeight(ocean),riverH=waterHeight(river);
        float h=mix(oceanH,riverH,vFlow.z);
        vec2 p=mix(ocean,river,vFlow.z);
        float dx=waterHeight(p+vec2(0.08,0.0))-waterHeight(p-vec2(0.08,0.0));
        float dz=waterHeight(p+vec2(0.0,0.08))-waterHeight(p-vec2(0.0,0.08));
        vec3 n=normalize(vec3(-dx*1.4,1.0,-dz*1.4));
        vec3 viewDir=normalize(cameraPosition-vWorld);
        vec3 halfDir=normalize(normalize(vec3(-0.45,0.85,0.3))+viewDir);
        float glint=pow(max(0.0,dot(n,halfDir)),120.0);
        float depth=smoothstep(0.01,0.5,vDepth);
        vec3 c=mix(shallowColor,deepColor,depth);
        c=mix(c,vec3(0.12,0.31,0.25),vStill*0.7);
        c*=0.86+h*0.32;
        float wavelet=pow(max(0.0,sin(p.y*8.0+noise2(p*0.8)*6.0)),18.0);
        float brokenWave=smoothstep(0.5,0.78,noise2(vec2(p.x*2.8,p.y*0.55)));
        float crest=wavelet*brokenWave*(0.16+vFlow.z*0.1);
        float foam=(1.0-smoothstep(0.008,0.045,vDepth))*smoothstep(0.4,0.72,noise2(vWorld.xz*9.0-vec2(flowTime*0.25)));
        float caustic=(1.0-depth)*smoothstep(0.73,0.84,noise2(p*2.9+vec2(flowTime*0.07)))*0.15;
        float fresnel=pow(1.0-max(0.0,dot(viewDir,n)),3.0);
        c=mix(c,vec3(0.7,0.91,0.86),(crest+foam*0.65+caustic)*(1.0-vStill*0.95));
        c+=vec3(0.065,0.085,0.08)*glint+vec3(0.06,0.08,0.1)*fresnel;
        float frozen=smoothstep(0.18,0.5,iceAmount*vClimate*(1.0-smoothstep(0.08,0.44,vDepth)*0.65));
        float crack=1.0-smoothstep(0.01,0.03,abs(noise2(vWorld.xz*5.0)-0.5));
        vec3 ice=mix(vec3(0.32,0.57,0.64),vec3(0.77,0.9,0.92),noise2(vWorld.xz*1.7)*0.65+0.35)-crack*0.1;
        c=mix(c,ice,frozen);
        gl_FragColor=vec4(c,1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  })
}
