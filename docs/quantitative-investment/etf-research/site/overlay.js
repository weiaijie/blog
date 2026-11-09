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
    get('attribution-view').onchange = null;
    get('gap-pair').onchange = null;
    get('gap-day').onchange = null;
    get('gap-ranks').replaceChildren();
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

  const names = {'510300':'沪深300','513500':'标普500','159920':'恒生','511010':'国债'};
  const columns = ['price','dividend','commission','slippage','net'];
  const currency = new Intl.NumberFormat('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:8});
  const format = n=>currency.format(Number(n));

  function partsTable(symbols, caption, account) {
    const wrap = document.createElement('div');
    wrap.className = 'table-wrap'; wrap.tabIndex = 0;
    const table = document.createElement('table');
    table.createCaption().textContent = caption;
    const head = table.createTHead().insertRow();
    for (const text of ['ETF','价格贡献','分红','佣金','滑点','净贡献']) {
      const th = document.createElement('th'); th.scope='col'; th.textContent=text; head.append(th);
    }
    const body = table.createTBody();
    function appendRow(row, label, parts) {
      const th = document.createElement('th'); th.scope='row'; th.textContent=label; row.append(th);
      for (const k of columns) row.insertCell().textContent = format(parts[k]);
    }
    for (const symbol of symbols) appendRow(body.insertRow(),names[symbol]+' '+symbol,account.byEtf[symbol]);
    appendRow(table.createTFoot().insertRow(),'合计',account.totals);
    wrap.append(table);
    return wrap;
  }

  function renderGap(data, anchor) {
    const pair = get('gap-pair'), day = get('gap-day'), ranks = get('gap-ranks');
    const gaps = data.attribution.dailyGaps;
    pair.replaceChildren(...Object.keys(gaps).map(key=>new Option(key.replace('-', ' 减 '),key)));
    pair.value = data.portfolios.find(p=>p.id!==anchor).id+'-'+anchor;
    const series = chart.addSeries(LightweightCharts.LineSeries,{
      color:'#675495',lineWidth:2,priceLineVisible:false,lastValueVisible:false,
      priceFormat:{type:'price',precision:2,minMove:0.01}},2);
    series.createPriceLine({price:0,color:'#838e92',lineWidth:1,lineStyle:2,axisLabelVisible:false});
    const markers = LightweightCharts.createSeriesMarkers(series,[]);
    let records;
    const signed = value=>Number(value)>0?'+'+format(value):format(value);
    function show(date) {
      const row = records.get(date);
      if (!row) return;
      day.value = date;
      const [target,base] = pair.value.split('-');
      get('gap-check').textContent = date+'　'+target+' 当日盈亏 '+signed(row.targetChange)+' 元，'+base+
        ' 当日盈亏 '+signed(row.referenceChange)+' 元。相减为 '+signed(row.change)+' 元，累计 '+signed(row.cumulative)+' 元。';
      get('gap-table').replaceChildren(partsTable(data.symbols,date+' · '+pair.value+'（元）',row));
    }
    function update() {
      const currentDay = day.value, gap = gaps[pair.value];
      records = new Map(gap.days.map(r=>[r.date,r]));
      series.setData(gap.days.map(r=>({time:r.date,value:Number(r.cumulative)})));
      day.replaceChildren(...gap.days.map(r=>new Option(r.date,r.date)));
      ranks.replaceChildren();
      const points = [];
      for (const [dates,up] of [[gap.increases,true],[gap.decreases,false]]) {
        const line = document.createElement('div'), title = document.createElement('strong');
        title.textContent = up?'差额增加最多':'差额减少最多'; line.append(title);
        if (!dates.length) line.append('无');
        for (const [i,date] of dates.entries()) {
          const rank=(up?'↑':'↓')+(i+1), button=document.createElement('button');
          button.type='button'; button.textContent=rank+' '+date+'　'+signed(records.get(date).change)+' 元';
          button.onclick=()=>show(date); line.append(button);
          points.push({time:date,position:up?'belowBar':'aboveBar',shape:up?'arrowUp':'arrowDown',
                       color:up?'#137063':'#a74b29',text:rank});
        }
        ranks.append(line);
      }
      markers.setMarkers(points.sort((a,b)=>a.time.localeCompare(b.time)));
      show(records.has(currentDay)?currentDay:gap.days[gap.days.length-1].date);
    }
    day.onchange=()=>show(day.value);
    chart.subscribeClick(event=>show(event.time));
    pair.onchange=()=>{
      update();
      const summary=get('attribution-view');
      if ([...summary.options].some(o=>o.value===pair.value)) {
        summary.value=pair.value;
        summary.onchange();
      }
    };
    update();
    return key=>{
      if (gaps[key] && pair.value!==key) {
        pair.value=key;
        update();
      }
    };
  }

  function renderAttribution(data, anchor) {
    const select = get('attribution-view'), periods = get('attribution-periods');
    const ids = data.portfolios.map(p=>p.id);
    select.replaceChildren();
    for (const id of ids.filter(id=>id!==anchor)) {
      select.add(new Option('差额 · '+id+' 减 '+anchor,id+'-'+anchor));
    }
    for (const id of ids) select.add(new Option('组合 '+id+' 本身',id));
    const syncGap = renderGap(data,anchor);
    function update() {
      periods.replaceChildren();
      const choice = select.value;
      syncGap(choice);
      for (const [title,span] of [['整个持有期',data.attribution.holding],
                                  ['组合 '+anchor+' 前高至谷底',data.attribution.peakToTrough[anchor]]]) {
        if (!span) {
          const note = document.createElement('p');
          note.textContent = '组合 '+anchor+' 没有收盘回撤，无峰谷区间。';
          periods.append(note);
          continue;
        }
        const diff = choice.includes('-');
        const account = diff ? span.differences[choice] : span.accounts[choice];
        const wrap = partsTable(data.symbols,title+' · '+span.start+' 至 '+span.end+' · '+choice,account);
        const note = document.createElement('p');
        if (diff) {
          const [target,base] = choice.split('-');
          note.textContent = '账户对账：'+target+' 的盈亏（'+format(span.accounts[target].accountChange)+'）减去 '+
            base+' 的盈亏（'+format(span.accounts[base].accountChange)+'）＝ '+format(account.accountChange)+' 元。';
        } else {
          note.textContent = '账户对账：期末 '+format(account.endEquity)+' 减期初 '+format(account.startEquity)+
            ' ＝ '+format(account.accountChange)+' 元。';
        }
        periods.append(wrap,note);
      }
    }
    select.onchange = update;
    update();
  }

  async function open(params, anchor, label, singleReplay) {
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
      renderAttribution(data,anchor);
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
