'use strict';
const $ = id => document.getElementById(id);
const names = {'510300':'沪深300 ETF','513500':'标普500 ETF','159920':'恒生指数 ETF','511010':'国债 ETF'};
const money = value => value.toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
const signed = value => (value > 0 ? '+' : '') + money(value);
let selected='510300', count=60, cursor=0, records=[], model, priceChart, candles, equityChart, equitySeries;
let busy=false;
function chartOptions() {
  return {autoSize:true,layout:{background:{color:'#ffffff'},textColor:'#53696b',fontSize:11,attributionLogo:false},
    grid:{vertLines:{color:'#f2f5f2'},horzLines:{color:'#e8eeeb'}},
    rightPriceScale:{borderVisible:false,minimumWidth:53},
    timeScale:{borderColor:'#e0e8e4',rightOffset:1,fixLeftEdge:true,minBarSpacing:.05},
    localization:{locale:'zh-CN',dateFormat:'yyyy-MM-dd'},
    crosshair:{mode:LightweightCharts.CrosshairMode.Normal}};
}
function initCharts(){
  priceChart=LightweightCharts.createChart($('candles'),chartOptions());
  candles=priceChart.addSeries(LightweightCharts.CandlestickSeries,{
    upColor:'#b54630',downColor:'#08745e',borderUpColor:'#a53a27',borderDownColor:'#006652',
    wickUpColor:'#b54630',wickDownColor:'#08745e',priceFormat:{type:'price',precision:3,minMove:.001}});
  priceChart.subscribeCrosshairMove(p=>{
    const bar=p.seriesData.get(candles);
    if(bar){cursor=records.findIndex(x=>x.time===bar.time);showBar(bar);}
    else if(records.length)showBar(records.at(-1));
  });
  equityChart=LightweightCharts.createChart($('equity'),{...chartOptions(),handleScroll:false,handleScale:false,
    leftPriceScale:{visible:false},rightPriceScale:{visible:false},timeScale:{visible:false},
    crosshair:{vertLine:{visible:false,labelVisible:false},horzLine:{visible:false,labelVisible:false}}});
  equitySeries=equityChart.addSeries(LightweightCharts.AreaSeries,{lineColor:'#276b60',lineWidth:2,topColor:'#cde6d9',bottomColor:'#fff',
    pointMarkersVisible:true,pointMarkersRadius:3,priceLineVisible:false,lastValueVisible:false});
}
function showBar(bar){
  $('bar-date').textContent=bar.time;
  for(const [id,key] of [['open','open'],['high','high'],['low','low'],['last','close']])$(id).textContent=bar[key].toFixed(3);
}
function setRange(){
  priceChart.timeScale().setVisibleLogicalRange({from:Math.max(-.5,records.length-(count || records.length)-.5),to:records.length+.5});
  document.querySelectorAll('[data-count]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.count)===count)));
}
function showFund(){
  if(!model)return;
  records=model.candles[selected].map(([time,open,high,low,close])=>({time,open,high,low,close}));
  priceChart.clearCrosshairPosition();candles.setData(records);setRange();
  const last=records.at(-1), prev=records.at(-2), delta=last.close-prev.close;
  cursor=records.length-1;showBar(last);
  $('fund').textContent=names[selected];$('code').textContent=selected;$('close').textContent=last.close.toFixed(3);
  $('change').textContent=(delta>0?'+':'')+(100*delta/prev.close).toFixed(2)+'%';
  $('change').className=delta>=0?'positive':'negative';
  $('quote-date').textContent=last.time+' 收盘';
  $('market-date').textContent='未复权 · '+records[0].time+' 至 '+last.time+' · '+records.length+' 根日 K' +
    (selected==='513500'?' · 2022-03-29 份额拆分停牌，当日无日 K':'');
  document.querySelectorAll('[data-code]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.code===selected)));
}
function showAccount(){
  const {curve,initial,sessions,asOf,nextSession}=model;
  const total=curve.at(-1)[1], gain=total-initial;
  $('days').textContent='第 '+sessions+' 天';$('asof').textContent='账户核验至 '+asOf;
  $('progress').textContent='已观察 '+sessions+' 个交易日，主账户累计'+(gain>=0?'盈利 ':'亏损 ')+money(Math.abs(gain))+' 元。';
  $('balance').textContent=money(total);
  const previous = curve.length>1 ? curve.at(-2)[1] : initial;
  const daily = total-previous;
  $('day-gain').textContent=signed(daily)+' 元';
  $('day-gain').className=daily>=0?'positive':'negative';
  $('gain').textContent=signed(gain)+' 元';
  $('gain').className=gain>=0?'positive':'negative';
  $('curve-note').textContent=curve[0][0].slice(5)+' — '+asOf.slice(5);
  $('curve-values').textContent=money(curve[0][1])+' → '+money(total)+' 元';
  equitySeries.setData(curve.map(([time,value])=>({time,value})));
  equityChart.timeScale().setVisibleLogicalRange({from:-.15,to:Math.max(1.15,curve.length-.85)});
  $('equity').setAttribute('aria-label','账户总资产从 '+money(curve[0][1])+' 元到 '+money(total)+' 元，共 '+sessions+' 个观测日');
  $('next').textContent=nextSession?nextSession+' 收盘后核验行情；通过后记下第 '+(sessions+1)+' 天的资产和盈亏。':'等待下一交易日历核验。';
}
function showCoverage(){
  const rows=$('coverage-rows');
  rows.replaceChildren();
  for(const code of ['510300','513500','159920','511010']){
    const item=model.coverage[code], row=rows.insertRow();
    const name=document.createElement('th');
    name.scope='row';name.textContent=names[code]+' '+code;row.append(name);
    const dates=row.insertCell();
    dates.dataset.label='日 K 起止';
    dates.textContent=item.quoteStart+' 至 '+item.quoteThrough;
    const count=row.insertCell();
    count.dataset.label='收盘数';
    count.textContent=item.quotes.toLocaleString('zh-CN');
    const cell=row.insertCell();
    cell.dataset.label='可回测区间';
    for(const [start,end] of item.backtestWindows){
      const line=document.createElement('span');
      line.textContent=start+' 至 '+end;cell.append(line);
    }
  }
}
async function refresh(){
  if(busy)return;busy=true;
  try{
    const response=await fetch('market-data.json',{cache:'no-store'});
    if(!response.ok)throw Error('行情读取失败');
    const incoming=await response.json();
    if(!incoming.curve?.length || !Object.keys(names).every(s=>incoming.candles?.[s]?.length>=2))throw Error('数据不完整');
    if(!priceChart)initCharts();
    if(!model || JSON.stringify(model)!==JSON.stringify(incoming)){
      model=incoming;showFund();showAccount();showCoverage();
    }
    $('error').hidden=true;
  }catch(e){
    $('error').hidden=false;$('error').textContent=model?'更新暂未成功，仍显示上次核验的数据。':'图表尚未载入，请检查网络后刷新本页。';
  }finally{busy=false;}
}
document.querySelectorAll('[data-code]').forEach(b=>b.addEventListener('click',()=>{selected=b.dataset.code;showFund();}));
document.querySelectorAll('[data-count]').forEach(b=>b.addEventListener('click',()=>{count=Number(b.dataset.count);if(model)setRange();}));
$('candles').addEventListener('keydown',event=>{
  if(!records.length||!['ArrowLeft','ArrowRight'].includes(event.key))return;
  event.preventDefault();cursor=Math.max(0,Math.min(records.length-1,cursor+(event.key==='ArrowLeft'?-1:1)));
  const bar=records[cursor], range=priceChart.timeScale().getVisibleLogicalRange();
  if(range && (cursor<range.from || cursor>range.to)){
    const width=range.to-range.from,from=event.key==='ArrowLeft'?cursor-.5:cursor-width+.5;
    priceChart.timeScale().setVisibleLogicalRange({from,to:from+width});
  }
  priceChart.setCrosshairPosition(bar.close,bar.time,candles);showBar(bar);
});
refresh();setInterval(()=>{if(!document.hidden)refresh();},60000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
