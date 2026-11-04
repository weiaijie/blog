'use strict';
const data=JSON.parse(document.getElementById('research-data').textContent);
const names={cash:'现金（零息）',equity_hold:'510300 买入持有',bond_hold:'511010 买入持有',monthly_20_80:'月度 20/80',monthly_50_50:'月度 50/50',trend_120:'固定 120 日趋势'};
const colors=['#849095','#bd6844','#218b91','#7c6cb2','#183e72','#6b8e3b'];
const pct=v=>(v*100).toFixed(2)+'%';
const num=v=>Number(v).toLocaleString('zh-CN',{maximumFractionDigits:2});
const cell=(v,cls='')=>{const e=document.createElement('td');e.textContent=v;if(cls)e.className=cls;return e;};
function table(body,rows){body.replaceChildren();for(const values of rows){const tr=document.createElement('tr');values.forEach((v,i)=>tr.appendChild(cell(v,i?'num':'')));body.appendChild(tr);}}
function drawChart(runs){const svg=document.getElementById('chart');svg.replaceChildren();const ns='http://www.w3.org/2000/svg';const make=(tag,attrs,text)=>{const e=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text)e.textContent=text;svg.appendChild(e);return e;};
 make('title',{},'模拟资产曲线：初始资产为100，每日收盘，费用场景下的历史结果');
 const all=runs.flatMap(r=>data.nav[r.run]);const lo=Math.floor(Math.min(...all)/5)*5,hi=Math.ceil(Math.max(...all)/5)*5;const span=hi-lo||1;
 const x=i=>64+i*890/(data.dates.length-1),y=v=>280-(v-lo)*240/span;
 for(let i=0;i<=4;i++){const v=lo+i*span/4;make('line',{x1:64,x2:954,y1:y(v),y2:y(v),stroke:'#dce5e6'});make('text',{x:54,y:y(v)+4,'text-anchor':'end',fill:'#536772','font-size':12},v.toFixed(1));}
 runs.forEach((r,i)=>make('polyline',{'data-run':r.run,points:data.nav[r.run].map((v,j)=>x(j).toFixed(2)+','+y(v).toFixed(2)).join(' '),fill:'none',stroke:colors[i],'stroke-width':2}));
 make('text',{x:64,y:311,fill:'#536772','font-size':12},data.dates[0]);make('text',{x:954,y:311,'text-anchor':'end',fill:'#536772','font-size':12},data.dates.at(-1));
}
function render(){const cost=document.getElementById('cost').value;const strategy=document.getElementById('strategy').value;const runs=data.results.filter(r=>r.scenario===cost);
 table(document.getElementById('baseline-rows'),runs.map(r=>[names[r.strategy],pct(r.annualized_scenario_return),pct(r.max_close_drawdown),num(r.ending_equity),r.trades,r.excluded_orders]));drawChart(runs);
 table(document.getElementById('sensitivity-rows'),data.sensitivity.filter(r=>r.scenario===cost&&r.strategy===strategy).map(r=>[num(r.initial_cash)+' 元',r.execution_delay_sessions+' 个交易日',pct(r.annualized_scenario_return),pct(r.max_close_drawdown),num(r.ending_cash),r.trades]));
 const main=runs.find(r=>r.strategy===strategy),e=data.evaluation[main.run];
 document.getElementById('rolling-range').textContent='252 个交易间隔滚动年化范围：'+pct(e.rolling_min)+' 至 '+pct(e.rolling_max)+'（'+e.rolling_count+' 个重叠窗口，不是独立实验）。';
 table(document.getElementById('fold-rows'),e.folds.map(f=>[f.test_first_session+' → '+f.test_last_session,f.trading_intervals+(f.partial_fold?'（不足一折）':''),pct(f.total_return),pct(f.annualized_scenario_return),pct(f.max_close_drawdown),f.trade_count]));
 document.getElementById('fee-description').textContent={low:'单边佣金万 1，最低 5 元，滑点 1 bp。',base:'单边佣金万 3，最低 5 元，滑点 5 bp。',high:'单边佣金千 1，最低 5 元，滑点 10 bp。'}[cost]+' 卖出税率 0 为假设；未扣期末变现费用。';
}
const strategy=document.getElementById('strategy');Object.entries(names).forEach(([k,v])=>{const o=document.createElement('option');o.value=k;o.textContent=v;strategy.appendChild(o);});strategy.value='monthly_50_50';
document.getElementById('cost').addEventListener('change',render);strategy.addEventListener('change',render);
const legend=document.getElementById('legend');Object.values(names).forEach((name,i)=>{const e=document.createElement('span');e.textContent=name;e.style.setProperty('--c',colors[i]);legend.appendChild(e);});
const sourceBody=document.getElementById('source-rows');data.sources.forEach(r=>{const tr=document.createElement('tr');const name=cell('');const a=document.createElement('a');a.href='../data/snapshots/'+data.source_snapshot+'/'+r.name+'.body';a.textContent=r.name;name.appendChild(a);tr.appendChild(name);tr.appendChild(cell(String(r.status),r.status===200?'pass':'fail'));tr.appendChild(cell(r.error||'已保存原始响应'));sourceBody.appendChild(tr);});render();
