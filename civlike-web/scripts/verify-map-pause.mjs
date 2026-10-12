import { chromium } from 'playwright'
import { writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

const browser=await chromium.launch(),page=await browser.newPage({viewport:{width:1440,height:1000}}),results=[]
const errors=[];page.on('pageerror',(e)=>errors.push(e.message))
try {
  for(let run=0;run<6;run++) {
    await page.goto(`${process.env.ELEMENT_PREVIEW_URL||'http://127.0.0.1:5173'}/?view=map-elements&element=vineyard`)
    await page.waitForSelector('.element-stage[data-loaded="true"]')
    await page.waitForTimeout(890)
    await page.getByRole('button',{name:'暂停动画',exact:true}).click()
    await page.waitForTimeout(200)
    const samples=[]
    for(let i=0;i<8;i++) {
      samples.push(await page.locator('.element-stage').evaluate((host)=>{
        const c=host.querySelector('canvas'),gl=c.getContext('webgl2'),w=gl.drawingBufferWidth,h=gl.drawingBufferHeight,b=new Uint8Array(w*h*4)
        gl.readPixels(0,0,w,h,gl.RGBA,gl.UNSIGNED_BYTE,b)
        let hash=2166136261;for(let i=0;i<b.length;i+=16)hash=Math.imul(hash^b[i],16777619)>>>0
        return {hash,w,h,growth:host.dataset.growth,organs:host.dataset.organs}
      }))
      await page.waitForTimeout(250)
    }
    results.push({run,samples})
    assert.equal(new Set(samples.map((s)=>JSON.stringify(s))).size,1,'Paused vineyard drift')
  }
  assert.deepEqual(errors,[])
}finally{
  await writeFile('artifacts/map-elements/pause-verification.json',JSON.stringify({results,errors},null,2)+'\n')
  await browser.close()
}
console.log(JSON.stringify({runs:results.length,errors}))
