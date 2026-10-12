import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/landforms'
await mkdir(output,{recursive:true})
const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'})
const errors=[],results=[],retries=[]
page.on('pageerror',(e)=>errors.push(e.message))
page.on('console',(m)=>{if(m.type()==='error')errors.push(m.text())})
async function pixels() {
  return page.locator('.element-stage canvas').evaluate((canvas)=>{
    const gl=canvas.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4)
    gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b)
    let hash=2166136261,n=0,minX=w,maxX=0,minY=h,maxY=0
    for(let i=0;i<b.length;i+=16){hash=Math.imul(hash^b[i],16777619)>>>0;if(Math.abs(b[i]-b[0])+Math.abs(b[i+1]-b[1])+Math.abs(b[i+2]-b[2])>35){n++;const x=i/4%w,y=Math.floor(i/4/w);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}
    return {hash,coverage:n/(w*h/4),bounds:[minX,minY,maxX,maxY],w,h}
  })
}
function framed(p) {assert(p.coverage>.007 && p.bounds[0]>0 && p.bounds[1]>0 && p.bounds[2]<p.w-1 && p.bounds[3]<p.h-1,'Blank or clipped canvas')}
async function shot(name) {
  const bytes=await page.screenshot({fullPage:true})
  for(let i=0;;i++){try {await writeFile(`${output}/${name}.png`,bytes);return}catch(e){if(i>=3||!['UNKNOWN','EBUSY','EPERM'].includes(e.code))throw e;retries.push({name,code:e.code,attempt:i+1});await page.waitForTimeout(400*(i+1))}}
}
async function settled(phase,snow) {
  await page.waitForFunction(({phase,snow})=>{
    const state=JSON.parse(document.querySelector('.element-stage').dataset.terrain)
    return Math.abs(state.phase-phase)<.0001 && Math.abs(state.snow-snow)<.0001
  },{phase,snow})
}
async function state() {return JSON.parse(await page.locator('.element-stage').getAttribute('data-terrain'))}
try {
  for(const id of ['grassland','rolling-hills','rocky-mountain','snow-peak']) {
    await page.setViewportSize({width:1440,height:1000})
    await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=${id}`)
    await page.waitForSelector(`.element-stage[data-asset="${id}"][data-loaded="true"][data-terrain]`)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click()
    await page.getByLabel('风力',{exact:true}).fill('0')
    const states=[]
    for(const [i,label] of ['春','夏','秋','冬'].entries()) {
      await page.getByRole('button',{name:label,exact:true}).click()
      await settled(i/4,(id==='snow-peak'?[.62,.42,.54,.96]:[.12,0,.04,.94])[i])
      const pixel=await pixels();framed(pixel);states.push({label,...await state(),...pixel});await shot(`${id}-${label}`)
    }
    assert.equal(new Set(states.map((s)=>s.hash)).size,4,`${id}: identical seasons`)
    await page.getByLabel('积雪',{exact:true}).fill('0');await settled(.75,0)
    const bare=await pixels();await shot(`${id}-bare`)
    await page.getByLabel('积雪',{exact:true}).fill('100');await settled(.75,1)
    assert.notEqual((await pixels()).hash,bare.hash,'Snow did not cover the surface');await shot(`${id}-snow`)
    await page.getByRole('button',{name:'夏',exact:true}).click();await settled(.25,id==='snow-peak'?.42:0)
    await page.getByRole('button',{name:'播放动画',exact:true}).click()
    const calm=await pixels();await page.waitForTimeout(550);assert.equal((await pixels()).hash,calm.hash,'Zero wind drift')
    await page.getByLabel('风力',{exact:true}).fill('80');await page.waitForTimeout(750)
    assert.notEqual((await pixels()).hash,calm.hash,'No wind motion')
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(200)
    const paused=await pixels();await page.waitForTimeout(450);assert.equal((await pixels()).hash,paused.hash,'Pause failed')
    const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'));assert(drawCalls<450)
    for(const view of ['正面','侧面','俯视']){await page.getByRole('button',{name:view,exact:true}).click();await page.waitForTimeout(250);framed(await pixels());await shot(`${id}-${view}`)}
    await page.getByRole('button',{name:'自由视角',exact:true}).click()
    for(const [width,height] of [[390,844],[320,720]]){
      await page.setViewportSize({width,height});await page.waitForTimeout(350);framed(await pixels())
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile overflow');await shot(`${id}-mobile-${width}`)
    }
    await page.getByLabel('四季循环',{exact:true}).check()
    await page.waitForFunction(()=>JSON.parse(document.querySelector('.element-stage').dataset.terrain).phase>.27)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click()
    const frozen=await state();await page.waitForTimeout(550);assert.deepEqual(await state(),frozen,'Season clock did not pause')
    await page.getByLabel('四季循环',{exact:true}).uncheck();await page.waitForTimeout(550)
    assert.deepEqual(await state(),frozen,'Disabling cycle jumped to an old season')
    assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes(id))
    results.push({id,states,drawCalls})
  }
  await page.getByLabel('选择模型',{exact:true}).selectOption('wheat-field')
  await page.waitForSelector('.element-stage[data-asset="wheat-field-v3"][data-loaded="true"]')
  assert.equal(await page.getByLabel('四季循环',{exact:true}).count(),0)
  assert.equal(await page.locator('.element-stage').getAttribute('data-terrain'),null)
  assert.deepEqual(errors,[])
  await writeFile(`${output}/verification.json`,JSON.stringify({results,retries,errors},null,2)+'\n')
  console.log(JSON.stringify({models:results.length,retries,errors}))
}finally {await browser.close()}
