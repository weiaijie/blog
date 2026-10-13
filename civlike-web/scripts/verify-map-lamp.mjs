import { chromium } from 'playwright'
import { mkdir,writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/street-lamp'
await mkdir(output,{recursive:true})
const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'})
const errors=[],stages=[],times=[],views=[],mobile=[]
page.on('pageerror',(e)=>errors.push(e.message));page.on('console',(m)=>{if(m.type()==='error')errors.push(m.text())})
async function state(){return JSON.parse(await page.locator('.element-stage').getAttribute('data-building'))}
async function pixels(){return page.locator('.element-stage canvas').evaluate((c)=>{
  const gl=c.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4)
  gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b)
  let hash=2166136261,n=0,minX=w,maxX=0,minY=h,maxY=0
  for(let i=0;i<b.length;i+=16){hash=Math.imul(hash^b[i],16777619)>>>0;if(Math.abs(b[i]-b[0])+Math.abs(b[i+1]-b[1])+Math.abs(b[i+2]-b[2])>35){n++;const x=i/4%w,y=Math.floor(i/4/w);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}
  return {hash,coverage:n/(w*h/4),framed:minX>0&&minY>0&&maxX<w-1&&maxY<h-1}
})}
async function shot(name){await writeFile(`${output}/${name}.png`,await page.screenshot({fullPage:true}))}
function framed(p){assert(p.coverage>.002&&p.framed,JSON.stringify(p))}
async function time(hour){await page.getByLabel('昼夜时刻',{exact:true}).fill(String(hour));await page.waitForFunction((h)=>JSON.parse(document.querySelector('.element-stage').dataset.building).lighting.hour===h,hour)}
try{
  await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=street-lamp`)
  await page.waitForSelector('.element-stage[data-asset="street-lamp"][data-loaded="true"][data-building]')
  await page.getByRole('button',{name:'暂停动画',exact:true}).click();await time(12)
  for(const progress of [0,30,52,78,100]){
    await page.getByLabel('施工进度',{exact:true}).fill(String(progress))
    await page.waitForFunction((p)=>Math.abs(JSON.parse(document.querySelector('.element-stage').dataset.building).progress-p)<.00001,progress/100)
    const p=await pixels();await shot(`stage-${progress}`);framed(p);stages.push({progress,...p})
    assert.equal((await state()).lighting.power,0)
  }
  assert.equal(new Set(stages.map((s)=>s.hash)).size,5)
  await page.getByLabel('升级附件',{exact:true}).check();await page.waitForTimeout(200)
  assert.notEqual((await pixels()).hash,stages.at(-1).hash);await shot('day-desktop')
  for(const hour of [12,18,22,6]){
    await time(hour);await page.waitForTimeout(200)
    const p=await pixels();framed(p);times.push({hour,...await state(),...p});await shot(`hour-${hour}`)
  }
  assert.equal(times[0].lighting.power,0);assert.equal(times[1].lighting.power,.5);assert.equal(times[2].lighting.power,1)
  assert.equal(times[3].lighting.power,.5);assert.equal(new Set(times.slice(0,3).map((s)=>s.hash)).size,3)
  await time(22);await page.getByLabel('照明供电',{exact:true}).uncheck();await page.waitForTimeout(200)
  assert.equal((await state()).lighting.power,0);assert.notEqual((await pixels()).hash,times[2].hash);await shot('power-off')
  await page.getByLabel('照明供电',{exact:true}).check();await page.waitForTimeout(150)
  assert.equal((await state()).lighting.power,1)
  for(const view of ['正面','侧面','俯视']){
    await page.getByRole('button',{name:view,exact:true}).click();await page.waitForTimeout(250)
    const p=await pixels();framed(p);views.push({view,...p});await shot(view)
  }
  await page.getByRole('button',{name:'自由视角',exact:true}).click();await time(18)
  await page.getByLabel('昼夜循环',{exact:true}).check();await page.getByRole('button',{name:'播放动画',exact:true}).click()
  const moving=await pixels();await page.waitForTimeout(500);assert.notEqual((await pixels()).hash,moving.hash)
  await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150)
  const paused=await state(),p=await pixels();await page.waitForTimeout(350);assert.deepEqual(await state(),paused);assert.equal((await pixels()).hash,p.hash)
  await page.getByLabel('运行速度',{exact:true}).fill('0');await page.getByRole('button',{name:'播放动画',exact:true}).click();await page.waitForTimeout(150)
  const stopped=await state();await page.waitForTimeout(350);assert.deepEqual(await state(),stopped)
  await page.getByLabel('运行速度',{exact:true}).fill('100');await time(22)
  const drawCalls=Number(await page.locator('.element-stage').getAttribute('data-draw-calls'));assert(drawCalls<100)
  for(const [width,height]of [[390,844],[320,720]]){
    await page.setViewportSize({width,height});await page.waitForTimeout(300);const p=await pixels();framed(p)
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));mobile.push({width,...p});await shot(`mobile-${width}`)
  }
  await page.getByLabel('自动施工',{exact:true}).check();await page.waitForTimeout(500)
  await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150)
  const construction=await state();await page.waitForTimeout(350);assert.deepEqual(await state(),construction);assert.equal(construction.lighting.power,0)
  assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes('street-lamp'))
  await page.getByLabel('选择模型',{exact:true}).selectOption('fence');await page.waitForSelector('.element-stage[data-asset="fence"][data-loaded="true"]')
  assert.equal(await page.getByLabel('昼夜时刻',{exact:true}).count(),0);assert.equal((await state()).lighting,undefined)
  assert.deepEqual(errors,[])
  await writeFile(`${output}/verification.json`,JSON.stringify({stages,times,views,mobile,drawCalls,errors},null,2)+'\n')
  console.log(JSON.stringify({stages:stages.length,times:times.length,views:views.length,mobile:mobile.length,drawCalls,errors}))
}finally{await browser.close()}
