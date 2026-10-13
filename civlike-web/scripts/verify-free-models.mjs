import { chromium } from 'playwright'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const output='artifacts/map-elements/free-models'
await mkdir(output,{recursive:true})
const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'})
const errors=[],results=[]
page.on('pageerror',(e)=>errors.push(e.message));page.on('console',(m)=>{if(m.type()==='error')errors.push(m.text())})
async function state(){return JSON.parse(await page.locator('.element-stage').getAttribute('data-skeletal'))}
async function pixels(){return page.locator('.element-stage canvas').evaluate((c)=>{
  const gl=c.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4)
  gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b)
  let hash=2166136261,n=0,minX=w,maxX=0,minY=h,maxY=0
  for(let i=0;i<b.length;i+=16){hash=Math.imul(hash^b[i],16777619)>>>0;if(Math.abs(b[i]-b[0])+Math.abs(b[i+1]-b[1])+Math.abs(b[i+2]-b[2])>35){n++;const x=i/4%w,y=Math.floor(i/4/w);minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y)}}
  return {hash,coverage:n/(w*h/4),framed:minX>0&&minY>0&&maxX<w-1&&maxY<h-1}
})}
function framed(p){assert(p.coverage>.005&&p.framed,`Blank or clipped: ${JSON.stringify(p)}`)}
async function shot(name){await writeFile(`${output}/${name}.png`,await page.screenshot({fullPage:true}))}
try {
  for(const [family,count,clips]of [['farmer',24,['Idle','Walk','Run','Wave']],['horse',13,['Idle','Walk','Gallop','Eating']]]) {
    await page.setViewportSize({width:1440,height:1000})
    await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=${family}&revision=3`)
    await page.waitForSelector(`.element-stage[data-asset="${family}-v3"][data-loaded="true"][data-skeletal]`)
    assert.equal((await state()).clips.length,count)
    assert.equal(await page.getByLabel('成长阶段',{exact:true}).count(),0)
    assert.equal(await page.getByLabel('生长阶段',{exact:true}).count(),0)
    const motions=[]
    for(const clip of clips) {
      await page.getByLabel('骨骼动作',{exact:true}).selectOption(clip);await page.waitForTimeout(550)
      const a=await pixels();framed(a);await page.waitForTimeout(400);assert.notEqual((await pixels()).hash,a.hash,`${family}/${clip} static`)
      await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(150)
      const paused=await pixels(),s=await state();await page.waitForTimeout(350)
      assert.equal((await pixels()).hash,paused.hash);assert.deepEqual(await state(),s);await shot(`${family}-${clip}`)
      motions.push({clip,...paused})
    }
    await page.getByLabel('骨骼动作',{exact:true}).selectOption('Idle');await page.waitForTimeout(400)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click();await page.waitForTimeout(100)
    for(const view of ['正面','侧面','背面']) {await page.getByRole('button',{name:view,exact:true}).click();await page.waitForTimeout(200);framed(await pixels());await shot(`${family}-${view}`)}
    await page.getByRole('button',{name:'自由视角',exact:true}).click()
    await page.getByLabel('动作速度',{exact:true}).fill('0');await page.getByRole('button',{name:'播放动画',exact:true}).click();await page.waitForTimeout(200)
    const frozen=await pixels();await page.waitForTimeout(400);assert.equal((await pixels()).hash,frozen.hash)
    await page.getByLabel('动作速度',{exact:true}).fill('150');await page.waitForTimeout(400);assert.notEqual((await pixels()).hash,frozen.hash)
    for(const [width,height]of [[390,844],[320,720]]) {await page.setViewportSize({width,height});await page.waitForTimeout(250);framed(await pixels());assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await shot(`${family}-mobile-${width}`)}
    assert((await page.getByLabel('下载 GLB',{exact:true}).getAttribute('download')).includes(`${family}-v3`))
    await page.getByRole('button',{name:'原版',exact:true}).click();await page.waitForSelector(`.element-stage[data-asset="${family}"][data-loaded="true"]`)
    assert.equal(await page.getByLabel('骨骼动作',{exact:true}).count(),0)
    await page.getByRole('button',{name:'免费模型',exact:true}).click();await page.waitForSelector(`.element-stage[data-asset="${family}-v3"][data-loaded="true"][data-skeletal]`)
    results.push({family,count,motions})
  }
  await page.getByLabel('选择模型',{exact:true}).selectOption('wheat-field');await page.waitForSelector('.element-stage[data-asset="wheat-field-v3"][data-loaded="true"]')
  assert.equal(await page.locator('.element-stage').getAttribute('data-skeletal'),null)
  assert.deepEqual(errors,[])
  await writeFile(`${output}/verification.json`,JSON.stringify({results,errors},null,2)+'\n')
  console.log(JSON.stringify({models:results.length,errors}))
} finally {await browser.close()}
