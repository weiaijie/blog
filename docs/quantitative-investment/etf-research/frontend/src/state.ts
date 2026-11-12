import {reactive,ref} from 'vue';
import {defaultPlan,parsePlan,type Plan,type Market,type Options} from './domain.ts';
export const plan=reactive<Plan>(parsePlan(defaultPlan));
export const notice=ref('');
export const market=ref<Market>();
export const options=ref<Options>();
export async function getJson<T>(url:string,signal?:AbortSignal):Promise<T>{
  const response=await fetch(url,{signal});
  let body;
  try{body=await response.json();}catch{throw Error('服务未返回可用JSON，请检查看板服务。');}
  if(!response.ok)throw Error(body.error||'数据暂不可用（'+response.status+'），请重试或查看运行状态。');
  return body as T;
}
let bootstrap:Promise<void>|undefined;
export function loadBase(force=false){if(force)bootstrap=undefined;return bootstrap??=(async()=>{
  const results=await Promise.allSettled([getJson<Market>('/market-data.json'),getJson<Options>('/api/v1/backtest/options')]);
  if(results[0].status==='fulfilled')market.value=results[0].value;
  if(results[1].status==='fulfilled')options.value=results[1].value;
  const failures=results.filter(r=>r.status==='rejected');
  if(failures.length){bootstrap=undefined;throw Error('部分状态加载失败，请重试。');}
})();}
export function applyPlan(value:unknown){Object.assign(plan,parsePlan(value));}
export function storedPlans():Plan[]{
  const value:unknown=JSON.parse(localStorage.getItem('etf.workbench.plans.v1')||'[]');
  if(!Array.isArray(value)||value.length>20)throw Error('本机方案列表损坏，请先导出当前方案。');
  return value.map(parsePlan);
}
export function savePlan(){
  const p=parsePlan(plan),old=storedPlans(),index=old.findIndex(x=>x.name===p.name);
  if(index>=0)old[index]=p;else{if(old.length>=20)throw Error('最多保存20套方案，请删除不再需要的方案后重试。');old.push(p);}
  localStorage.setItem('etf.workbench.plans.v1',JSON.stringify(old));
}
export function download(name:string,data:unknown){
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
