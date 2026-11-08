const sameWindowView = (() => {
  'use strict';
  const get = id => document.getElementById(id);
  const colors = {A:'#137063',B:'#a74b29',C:'#4958a4'};
  const money = new Intl.NumberFormat('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  const pct = n => (100*Number(n)).toFixed(2)+'%';
  let chart, controller;

  function clear() {
    controller?.abort();
    controller = null;
    chart?.remove();
    chart = null;
    get('overlay').hidden = true;
    get('overlay-body').hidden = true;
    get('overlay-single').onclick = null;
  }

  function render(data) {
    const portfolios = data.portfolios, leaders = data.leaders;
    const names = ids => ids.join('、');
    const recovery = leaders.firstRecovery.length ? '最早收复前高：'+names(leaders.firstRecovery) :
      portfolios.every(p=>p.recoveryState==='no_drawdown') ? '各组均无收盘回撤。' : '有回撤的组合均未在期内收复前高。';
    get('overlay-summary').textContent = '到期盈亏最高：'+names(leaders.highestPnl)+'　最大回撤最小：'+names(leaders.shallowestDrawdown)+'　'+recovery;
    const legend = get('overlay-legend'), rows = get('overlay-rows');
    legend.replaceChildren(); rows.replaceChildren();
    chart = LightweightCharts.createChart(get('overlay-chart'),{autoSize:true,
      layout:{attributionLogo:false,textColor:'#526b70',panes:{separatorColor:'#bbcfc8'}},
      localization:{locale:'zh-CN',dateFormat:'yyyy-MM-dd'},
      grid:{vertLines:{visible:false},horzLines:{color:'#ebefed'}},
      timeScale:{borderVisible:false}});
    for (const p of portfolios) {
      const label = document.createElement('span');
      label.style.borderColor = colors[p.id];
      label.textContent = '组合 '+p.id+' · '+p.weights.split(',').join(' / ');
      legend.append(label);
      for (const [pane,field] of ['nav','drawdown'].entries()) {
        const series = chart.addSeries(LightweightCharts.LineSeries,{color:colors[p.id],lineWidth:2,
          priceLineVisible:false,lastValueVisible:false,priceFormat:{type:'custom',minMove:.0001,
            formatter:field==='nav' ? n=>n.toFixed(4) : pct}},pane);
        series.setData(p.daily.map(point=>({time:point.date,value:Number(point[field])})));
      }
      const s = p.summary, noDip = p.recoveryState==='no_drawdown', row = rows.insertRow();
      const th = document.createElement('th'); th.scope='row'; th.textContent=p.id; row.append(th);
      const recovered = noDip?'无回撤':s.recovery || '期末未收复';
      for (const value of [money.format(s.pnl)+' 元',pct(s.max_drawdown),noDip?'—':s.peak,
        noDip?'—':s.trough,recovered,p.recoveryState==='recovered'?s.peak_to_recovery_sessions:'—']) {
        row.insertCell().textContent = value;
      }
    }
    function showDate(time) {
      const daily = portfolios[0].daily;
      const i = daily.findIndex(point=>point.date===time);
      const index = i<0?daily.length-1:i;
      const values = portfolios.map(p=>p.id+' 净值 '+Number(p.daily[index].nav).toFixed(4)+' / 回撤 '+pct(p.daily[index].drawdown));
      get('overlay-point').textContent = daily[index].date+'　'+values.join('　');
    }
    chart.subscribeCrosshairMove(event=>showDate(event.time));
    chart.timeScale().fitContent();
    showDate(null);
  }

  async function open(params, label, singleReplay) {
    clear();
    const current = new AbortController();
    controller = current;
    const section = get('overlay'), status = get('overlay-status');
    section.hidden = false;
    get('overlay-title').textContent = label+'最差一期 · 同区间对比';
    status.textContent = params.start+' 至 '+params.end+' · 正在重放各组合…';
    section.scrollIntoView({block:'start'});
    const url = 'api/v1/backtest/overlay?'+new URLSearchParams(params);
    try {
      const res = await fetch(url,{signal:current.signal});
      const data = await res.json();
      if (!res.ok) throw Error(data.error || '服务不可用');
      if (controller!==current) return;
      get('overlay-body').hidden = false;
      render(data);
      const s = data.portfolios[0].summary;
      status.textContent = s.start+' 至 '+s.end+' · '+s.sessions+' 个交易日 · 每组期初 '+money.format(params.capital)+' 元';
      get('overlay-json').href = url;
      get('overlay-single').onclick = singleReplay;
    } catch (err) {
      if (controller===current) {
        get('overlay-body').hidden = true;
        status.textContent = '同区间对比读取失败。'+err.message;
      }
    }
  }
  return {open,clear};
})();
