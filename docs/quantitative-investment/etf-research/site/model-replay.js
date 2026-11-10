function setupModelReplay(parameters, coverage) {
  'use strict';
  const el = id => document.getElementById('replay-' + id);
  const names = {'510300':'沪深300','513500':'标普500','159920':'恒生','511010':'国债'};
  const reasons = {initial:'首次建仓，按起始配比',monthly:'月初调回目标配比',
    trend_on:'沪深300含分红指数高于120日均线，股债各50%',trend_off:'沪深300含分红指数未高于120日均线，国债100%'};
  const fills = {filled:'已成交',cash_limited:'可用现金有限',cash_limited_partial_or_zero:'可用现金有限',
    known_ex_dividend_day:'除息日保护',opening_halt:'开盘停牌',conservative_9pct_buffer:'价格保护'};
  const money = n => Number(n).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  let query, frames = [], shown = 0, total = 0, chart, series, timer, request, enabled = false;
  const strategy=mountStrategyControls(()=>reset(enabled));
  function setRanges() {
    const opts=coverage();
    if (!opts) return;
    const params=parameters(), weights=params.get('weights').split(',').map(Number);
    const trend=strategy.model==='trend_120';
    const split=!trend && weights[1]>0;
    const first=trend ? opts.trendFirst : split ? opts.first : weights[2]>0 ? opts.overseasFirst : opts.domesticFirst;
    const menu=el('range');
    menu.replaceChildren(new Option('上方日期 · '+params.get('start')+' 至 '+params.get('end'),'custom'),
      new Option('连续区间 · '+first+' 至 '+opts.last,first+'/'+opts.last));
    if (params.get('start')===opts.defaults.start && params.get('end')===opts.last && !new URLSearchParams(location.search).has('start')) {
      menu.selectedIndex=1;
    }
    if (split) menu.add(new Option('拆分前 · '+opts.overseasFirst+' 至 '+opts.preSplitLast,opts.overseasFirst+'/'+opts.preSplitLast));
  }
  function endpoint(step) {
    const params = new URLSearchParams(query);
    params.set('step', step);
    return 'api/v1/backtest/replay?' + params;
  }
  function buttons() {
    el('start').disabled = !enabled;
    el('step').disabled = !!request || !!timer || shown >= total;
    el('auto').disabled = !!request || shown >= total;
    el('auto').textContent = timer ? '暂停' : '自动走完';
  }
  function stop() { clearInterval(timer); timer = null; buttons(); }
  function reset(single, keepRange=false) {
    const selected=el('range').value;
    setRanges();
    if (keepRange && [...el('range').options].some(o=>o.value===selected)) el('range').value=selected;
    document.body.classList.remove('playing-model');
    enabled = single;
    request?.abort(); request = null;
    stop(); frames = []; shown = total = 0;
    document.getElementById('replay').hidden = !single;
    el('body').hidden = true;
    el('status').textContent = '';
    strategy.rebalance=parameters().get('rebalance');
    el('start').textContent = '开始回放';
    if (chart) { chart.remove(); chart = series = null; }
    buttons();
  }
  function candle(frame) {
    const bar = frame.bars[el('symbol').value];
    return {time:frame.date, open:+bar.open, high:+bar.high, low:+bar.low, close:+bar.close};
  }
  function mark() {
    const bar = candle(frames[shown-1]);
    el('ohlc').textContent = '开 '+bar.open.toFixed(3)+'　高 '+bar.high.toFixed(3)+'　低 '+bar.low.toFixed(3)+'　收 '+bar.close.toFixed(3);
  }
  function describe(units) {
    return Object.entries(units).map(([s,n])=>names[s]+' '+n+' 份').join('、');
  }
  function trigger(plan) {
    if (plan.reason==='installment') return '第 '+plan.batch+' / '+plan.installments+' 批，目标投入总资产的 '+(100*plan.batch/plan.installments).toFixed(1)+'%';
    if (plan.trendSpread != null) return reasons[plan.reason]+'（窗口首日指数为1，指数减均线 '+Number(plan.trendSpread).toFixed(5)+'）';
    return reasons[plan.reason];
  }
  let markers, trades=[];
  function paintTrades() {
    const symbol=el('symbol').value;
    markers.setMarkers(trades.filter(o=>o.symbol===symbol).map(o=>({
      time:o.day, position:o.side==='buy'?'belowBar':'aboveBar', shape:o.side==='buy'?'arrowUp':'arrowDown',
      color:o.side==='buy'?'#185948':'#9d4838', text:o.side==='buy'?'买':'卖'
    })));
  }
  function display(step) {
    const row = frames[step-1], previousPlan = frames[step-2]?.nextPlan;
    if (!shown) {
      document.body.classList.add('playing-model');
      el('body').hidden = false;
      el('symbol').replaceChildren(...Object.keys(row.bars).map(s=>new Option(names[s]+' · '+s,s)));
      chart = LightweightCharts.createChart(el('candles'),{autoSize:true,layout:{attributionLogo:false},
        rightPriceScale:{minimumWidth:55},timeScale:{minBarSpacing:2}});
      series = chart.addSeries(LightweightCharts.CandlestickSeries,{upColor:'#b34836',downColor:'#19735d',
        wickUpColor:'#b34836',wickDownColor:'#19735d',borderVisible:false,priceFormat:{type:'price',precision:3,minMove:.001}});
    }
    if (!shown) {trades=[];markers=LightweightCharts.createSeriesMarkers(series,[]);}
    let newTrades=false;
    for (let i=shown;i<step;i++) {
      const frame=frames[i];
      series.update(candle(frame));
      for (const o of frame.orders) if (o.filled>0) {trades.push({...o,day:frame.date});newTrades=true;}
    }
    if (newTrades) paintTrades();
    shown = step;
    chart.timeScale().setVisibleLogicalRange({from:Math.max(-1,step-55),to:Math.max(step+2,10)});
    mark();
    el('date').textContent = row.date+'　'+step+' / '+total+' 日';
    el('equity').textContent = money(row.equity)+' 元';
    el('pnl').textContent = '当日盈亏 '+money(row.dayPnl)+' 元 · 累计 '+money(row.pnl)+' 元';
    el('cash').textContent = '可用现金 '+money(row.availableCash)+' 元 · 应收分红 '+money(row.receivables)+' 元 · 距前高 '+(100*row.drawdown).toFixed(2)+'%';
    el('holdings').textContent = describe(row.holdings);
    el('reason').textContent = previousPlan ? previousPlan.signal+' 收盘决定：'+trigger(previousPlan)+(row.orders.length?'。':'。当前持仓已达目标。') :
      (step===1?'首日以现金起步。':'沿用持仓，今天没有待执行调仓。');
    el('orders').replaceChildren(...row.orders.map(o=>{
      const li=document.createElement('li');
      li.textContent=names[o.symbol]+(o.side==='buy'?' 买入':' 卖出')+'：计划 '+o.requested+' 份，成交 '+o.filled+' 份'+
        (o.price?'，模拟价 '+Number(o.price).toFixed(3)+' 元，佣金 '+money(o.fee)+' 元':'')+'（'+fills[o.reason]+'）。';
      return li;
    }));
    el('plan').textContent = row.nextPlan ? trigger(row.nextPlan)+'。'+row.nextPlan.execution+' 开盘目标持仓：'+describe(row.nextPlan.target)+'。'+Object.entries(row.nextPlan.change).filter(([,n])=>n!==0).map(([s,n])=>names[s]+(n>0?'计划买入':'计划卖出')+Math.abs(n)+' 份').join('、') :
      (shown===total?'已到所选区间末日。':'下一交易日维持现有持仓。');
    el('json').href = endpoint(shown);
    el('start').textContent = '从头回放';
    el('status').textContent = shown===total ? '回放完成。' : '';
    buttons();
  }
  async function load(step) {
    const current = new AbortController();
    request = current; buttons();
    el('status').textContent = '正在核算…';
    try {
      const res = await fetch(endpoint(step),{signal:current.signal});
      const data = await res.json();
      if (!res.ok) throw Error(data.error || '服务暂时不可用。');
      if (current !== request) return false;
      frames = data.frames; total = data.totalSessions;
      return true;
    } catch (err) {
      if (current === request) el('status').textContent = '回放失败。'+err.message;
      return false;
    } finally {
      if (current === request) {request=null; buttons();}
    }
  }
  el('exit').onclick = ()=>{reset(true);el('start').focus();};
  el('range').onchange = ()=>reset(enabled,true);
  el('symbol').onchange = ()=>{series.setData(frames.slice(0,shown).map(candle));paintTrades();mark();};
  el('start').onclick = async ()=>{
    reset(true,true); query = parameters(); query.set('model',strategy.model);
    if (strategy.model==='installments') query.set('installments',strategy.batches);
    if (el('range').value !== 'custom') {
      const [start,end] = el('range').value.split('/');
      query.set('start',start); query.set('end',end);
    }
    if (strategy.model === 'trend_120') {query.set('weights','1,0,0,1');query.set('rebalance','monthly');}
    if (await load(1)) display(1);
  };
  el('step').onclick = async ()=>{
    if (shown < frames.length || await load(shown+1)) display(shown+1);
  };
  el('auto').onclick = async ()=>{
    if (timer) {stop();return;}
    if (frames.length !== total && !await load('all')) return;
    timer=setInterval(()=>{
      display(shown+1);
      if (shown===total) stop();
    },Math.max(20,Math.min(250,8000/(total-shown))));
    buttons();
  };
  return {reset};
}
