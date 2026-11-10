(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const form = get('work-form');
  const fields = form.elements;
  const cards = get('portfolio-cards');
  const compare = get('work-compare');
  const comparison = get('comparison');
  const inputsOf = card => [...card.querySelectorAll('[data-weight]')];
  const vectorOf = card => inputsOf(card).map(i=>i.value).join(',');
  const run = get('work-run');
  const windows = get('work-windows');
  const cohorts = get('work-cohorts');
  const status = get('work-status');
  const result = get('work-result');
  const amount = new Intl.NumberFormat('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
  const percent = n => (Number(n)*100).toFixed(2)+'%';
  const buttons = [...document.querySelectorAll('[data-view]')];
  let coverage;
  let chart, series, response, view = 'drawdown', generation = 0, controller, downloadUrl;
  function parameters() {
    return new URLSearchParams({start:fields.start.value,end:fields.end.value,capital:fields.capital.value,
      weights:[...cards.children].map(vectorOf).join('|'),rebalance:fields.rebalance.value,fees:fields.fees.value});
  }
  const player = setupModelReplay(parameters);
  function mix(card) {
    const weights = inputsOf(card), preset = card.querySelector('[data-preset]');
    const values = weights.map(input=>Number(input.value));
    const total = values.reduce((a,b)=>a+b,0);
    card.querySelector('[data-mix]').textContent = total > 0 && values.every(n=>Number.isFinite(n) && n>=0)
      ? '折算仓位（按上方顺序） '+values.map(n=>percent(n/total)).join(' / ') : '请给至少一只 ETF 填写正数。';
    weights[0].setCustomValidity(total > 0 ? '' : '目标配比合计须大于零。');
    const raw = weights.map(i=>i.value).join(',');
    preset.value = [...preset.options].some(o=>o.value===raw) ? raw : '';
  }
  function setWeights(card, vector) {
    const values = vector.split(',');
    inputsOf(card).forEach((input,i)=>{
      input.min='0'; input.max='99999.99'; input.step='.01'; input.value=values[i] ?? '';
    });
    mix(card);
  }
  function updateControls() {
    const n = cards.children.length;
    run.hidden = windows.hidden = n > 1;
    compare.hidden = n === 1;
    document.querySelector('a[href="#replay"]').hidden = n > 1;
    get('add-portfolio').hidden = n === 3;
    get('remove-portfolio').hidden = n === 1;
  }
  function addCard(vector) {
    const card = cards.firstElementChild.cloneNode(true);
    card.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));
    card.querySelector('legend').textContent = '组合 '+'ABC'[cards.children.length]+' 配比';
    cards.append(card);
    setWeights(card,vector);
    updateControls();
  }
  function updateDates() {
    if (!coverage) return;
    const overseas = [...cards.children].some(card=>inputsOf(card).slice(1,3).some(i=>Number(i.value)>0));
    const sp = [...cards.children].some(card=>Number(inputsOf(card)[1].value)>0);
    const first = overseas ? coverage.overseasFirst : coverage.domesticFirst;
    get('work-pre-split').hidden = !sp;
    for (const input of [fields.start,fields.end]) {input.min=first;input.max=coverage.last;}
    get('work-limits').textContent = (overseas?'含跨境 ETF 的共同回测区间 ':'沪深300与国债可用区间 ')+first+
      ' 至 '+coverage.last+'。'+(sp?'标普 ETF 在 '+coverage.splitDay+' 拆分停牌，请选择拆分前或复牌后的区间。':'')+
      '休市端点取区间内交易日。使用场内人民币价格与分红，起点后的首个开盘模拟建仓。';
  }
  function changed() {
    player.reset(cards.children.length === 1);
    updateDates();
    generation++;
    sameWindowView.clear();
    controller?.abort();
    run.disabled = windows.disabled = compare.disabled = false;
    comparison.hidden = cohorts.hidden = true;
    result.hidden = true;
    status.textContent = '参数已修改，点击运行查看结果。';
  }
  form.addEventListener('input', event=>{
    if (event.target.matches('[data-preset]')) return;
    if (event.target.matches('[data-weight]')) mix(event.target.closest('fieldset'));
    changed();
  });
  cards.addEventListener('change', event=>{
    const preset = event.target;
    if (!preset.matches('[data-preset]')) return;
    const card = preset.closest('fieldset');
    if (!preset.value) { inputsOf(card)[0].focus(); return; }
    setWeights(card,preset.value);
    changed();
  });
  get('add-portfolio').addEventListener('click',()=>{
    addCard(cards.children.length===1?'1,0,0,1':'3,1,0,6');
    changed();
  });
  get('remove-portfolio').addEventListener('click',()=>{
    cards.lastElementChild.remove();
    updateControls();
    changed();
  });
  function showPoint(point) {
    get('work-point').textContent = point.date+'　总资产 '+amount.format(point.equity)+' 元　距前高 '+percent(point.drawdown);
  }
  function plot() {
    if (!chart) {
      chart = LightweightCharts.createChart(get('work-chart'),{autoSize:true,layout:{attributionLogo:false,textColor:'#526b70'},
        localization:{locale:'zh-CN',dateFormat:'yyyy-MM-dd'},grid:{vertLines:{visible:false},horzLines:{color:'#ebefed'}}});
      chart.subscribeCrosshairMove(event=>{
        const point = response?.daily.find(row=>row.date===event.time);
        if (response) showPoint(point || response.daily.at(-1));
      });
    }
    if (series) chart.removeSeries(series);
    const dd = view === 'drawdown';
    series = chart.addSeries(LightweightCharts.AreaSeries,{lineColor:dd?'#9d4838':'#23705f',
      topColor:dd?'#e5b7ab':'#8abfac',bottomColor:'#ffffff',priceLineVisible:false,
      priceFormat:{type:'custom',minMove:.01,formatter:n=>dd?n.toFixed(2)+'%':amount.format(n)}});
    series.setData(response.daily.map(p=>({time:p.date,value:dd?Number(p.drawdown)*100:Number(p.equity)})));
    chart.timeScale().fitContent();
    buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
    showPoint(response.daily.at(-1));
  }
  buttons.forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;plot();}));
  function display(data, params, url) {
    response = data;
    const s = data.summary;
    result.hidden = false;
    get('work-range').textContent = s.start+' 至 '+s.end+' · '+s.sessions+' 个交易日';
    get('work-numbers').replaceChildren();
    for (const [label,value] of [['期末资产',amount.format(s.ending_equity)+' 元'],['净盈亏',amount.format(s.pnl)+' 元'],
      ['累计收益',percent(s.total_return)],['最大收盘回撤',percent(s.max_drawdown)]]) {
      const block = document.createElement('div'), strong = document.createElement('strong');
      strong.textContent = value;
      block.append(label,strong);
      get('work-numbers').append(block);
    }
    get('work-recovery').textContent = Number(s.max_drawdown) === 0 ? '期间未出现收盘回撤。' :
      '从 '+s.peak+' 的前高跌至 '+s.trough+' 的谷底，减少 '+amount.format(s.peak_to_trough_loss)+' 元。'+
      (s.recovery?'于 '+s.recovery+' 收复前高，共 '+s.peak_to_recovery_sessions+' 个交易日。':'截至期末仍未收复前高。');
    const page = new URL(location.href);
    page.search = params.toString();
    page.hash = 'workbench';
    get('work-permalink').href = page.href;
    get('work-json').href = url;
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    downloadUrl = URL.createObjectURL(new Blob([JSON.stringify(data)],{type:'application/json'}));
    get('work-download').href = downloadUrl;
    plot();
  }
  function showWorst(period, label) {
    const replay = period.worstReplay, replayParams = new URLSearchParams(replay.parameters);
    view = 'drawdown';
    display(replay,replayParams,'api/v1/backtest?'+replayParams.toString());
    get('work-range').prepend(label+'最差一期 · ');
    result.scrollIntoView({block:'start'});
  }
  function displayComparison(data, params, url) {
    const portfolios = data.portfolios;
    const first = portfolios[0];
    get('comparison-range').textContent = first.firstSession+' 至 '+first.lastSession+' · 每组每次从 '+amount.format(data.parameters.capital)+' 元起步';
    const tables = get('comparison-tables');
    tables.replaceChildren();
    for (const years of ['1','2']) {
      const wrap = document.createElement('div');
      wrap.className = 'table-wrap';
      wrap.tabIndex = 0;
      const table = document.createElement('table');
      table.createCaption().textContent = '持有 '+years+' 年';
      const head = table.createTHead().insertRow();
      for (const label of ['指标', ...portfolios.map(p=>'组合 '+p.id)]) {
        const th = document.createElement('th');
        th.scope = 'col'; th.textContent = label; head.append(th);
      }
      portfolios.forEach((p,i)=>{
        const weightsLabel = document.createElement('small');
        weightsLabel.textContent = p.parameters.weights.split(',').join(' / ');
        head.cells[i+1].append(weightsLabel);
      });
      const body = table.createTBody();
      const metrics = [
        ['满期次数', p=>p.count],
        ['赚钱次数', p=>p.profitable+' / '+p.count],
        ['年化 ≥ 4% 次数', p=>p.reached+' / '+p.count],
        ['最差到期盈亏', p=>(p.worstPnl>0?'+':'')+amount.format(p.worstPnl)+' 元（'+percent(p.worstReturn)+'）']
      ];
      for (const [label,format] of metrics) {
        const row = body.insertRow(), th = document.createElement('th');
        th.scope = 'row'; th.textContent = label; row.append(th);
        for (const portfolio of portfolios) {
          const period = portfolio.periods[years];
          row.insertCell().textContent = period.count || label==='满期次数' ? format(period) : '—';
        }
      }
      const last = body.insertRow(), th = document.createElement('th');
      th.scope = 'row'; th.textContent = '最差一期'; last.append(th);
      for (const portfolio of portfolios) {
        const p = portfolio.periods[years], cell = last.insertCell();
        if (!p.count) { cell.textContent = '没有满期窗口'; continue; }
        const button = document.createElement('button'), date = document.createElement('small');
        button.type = 'button'; button.textContent = '同区间对比';
        const label = '组合 '+portfolio.id+' · '+years+' 年';
        button.setAttribute('aria-label',label+'最差期同区间对比');
        button.addEventListener('click',()=>{
          result.hidden = true;
          sameWindowView.open(data.overlays[portfolio.id][years],portfolio.id,label,()=>showWorst(p,label));
        });
        date.textContent = p.worstStart+' 至 '+p.worstEnd+(p.worstTies>1?'（并列 '+p.worstTies+' 次）':'');
        cell.append(button,date);
      }
      wrap.append(table); tables.append(wrap);
    }
    const page = new URL(location.href);
    page.search = params.toString(); page.searchParams.set('mode','compare'); page.hash = 'workbench';
    get('compare-permalink').href = page.href;
    get('compare-json').href = url;
    comparison.hidden = false;
  }
  function displayWindows(data, params, url) {
    const rows = get('cohort-rows');
    rows.replaceChildren();
    cohorts.hidden = false;
    get('cohort-range').textContent = data.firstSession+' 至 '+data.lastSession+' · 每次从 '+amount.format(data.parameters.capital)+' 元起步';
    for (const [years, period] of Object.entries(data.periods)) {
      const row = rows.insertRow();
      const heading = document.createElement('th');
      heading.scope = 'row';
      heading.textContent = years+' 年';
      row.append(heading);
      row.insertCell().textContent = period.count;
      if (!period.count) {
        const empty = row.insertCell();
        empty.colSpan = 4;
        empty.textContent = '没有满期窗口，可扩大日期范围后再运行。';
        continue;
      }
      for (const n of [period.profitable,period.reached]) {
        row.insertCell().textContent = n+'（'+percent(n/period.count)+'）';
      }
      row.insertCell().textContent = (period.worstPnl>0?'+':'')+amount.format(period.worstPnl)+' 元（'+percent(period.worstReturn)+'）';
      const cell = row.insertCell(), link = document.createElement('button'), dates = document.createElement('small');
      link.type = 'button';
      link.textContent = '查看 '+years+' 年最差期回撤';
      dates.textContent = period.worstStart+' 至 '+period.worstEnd+(period.worstTies>1?'（并列 '+period.worstTies+' 次）':'');
      link.addEventListener('click',()=>showWorst(period,years+' 年'));
      cell.append(link,dates);
    }
    const headers = rows.closest('table').tHead.rows[0].cells;
    for (const cell of rows.querySelectorAll('td')) {
      if (cell.colSpan === 1) cell.dataset.label = headers[cell.cellIndex].textContent;
    }
    const page = new URL(location.href);
    page.search = params.toString();
    page.searchParams.set('mode','windows');
    page.hash = 'workbench';
    get('cohort-permalink').href = page.href;
    get('cohort-json').href = url;
  }
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    player.reset(cards.children.length === 1);
    const token = ++generation;
    sameWindowView.clear();
    controller?.abort();
    controller = new AbortController();
    const comparing = cards.children.length > 1;
    const scanning = comparing || event.submitter === windows;
    run.disabled = windows.disabled = compare.disabled = true;
    comparison.hidden = cohorts.hidden = true;
    result.hidden = true;
    status.textContent = scanning ? '正在逐个交易日重新建仓并计算满期结果…' : '正在按所选参数从现金起步回放…';
    const endpoint = comparing ? 'compare' : 'windows';
    const params = parameters(), url = 'api/v1/backtest'+(scanning?'/'+endpoint:'')+'?'+params.toString();
    try {
      const res = await fetch(url,{signal:controller.signal});
      const data = await res.json();
      if (!res.ok) throw Error(data.error || '服务暂时不可用。');
      if (token !== generation) return;
      if (comparing) displayComparison(data,params,url);
      else if (scanning) displayWindows(data,params,url);
      else display(data,params,url);
      status.textContent = '回测完成。';
    } catch (err) {
      if (token === generation) {result.hidden = true;status.textContent = '运行失败。'+err.message;}
    } finally {if (token === generation) run.disabled = windows.disabled = compare.disabled = false;}
  });
  async function setup() {
    try {
      const res = await fetch('api/v1/backtest/options');
      if (!res.ok) throw Error();
      const config = await res.json(), query = new URLSearchParams(location.search);
      const params = Object.fromEntries(config.required.map(k=>[k,query.get(k) ?? config.defaults[k]]));
      for (const key of ['start','end','capital','fees','rebalance']) fields[key].value = params[key];
      coverage = config;
      const vectors = query.get('mode')==='compare' ? params.weights.split('|') : [params.weights];
      if (vectors.length>3 || (query.get('mode')==='compare' && vectors.length<2)) throw Error();
      setWeights(cards.firstElementChild,vectors[0]);
      vectors.slice(1).forEach(addCard);
      updateControls();
      player.reset(cards.children.length === 1);
      updateDates();
      get('work-pre-split').addEventListener('click',()=>{
        fields.start.value=config.overseasFirst;
        fields.end.value=config.preSplitLast;
        changed();
      });
      get('work-all-dates').addEventListener('click',()=>{
        fields.start.value = get('work-pre-split').hidden ? fields.start.min : config.first;
        fields.end.value = config.last;
        changed();
      });
      run.disabled = windows.disabled = compare.disabled = get('add-portfolio').disabled = false;
      if (config.required.every(k=>query.has(k))) {
        const submit = cards.children.length>1 ? compare : (query.get('mode')==='windows'?windows:run);
        form.requestSubmit(submit);
      }
    } catch {status.textContent = '回测服务暂时不可用，请刷新重试。';}
  }
  setup();
})();
