(() => {
  'use strict';
  const get = id => document.getElementById(id);
  const form = get('work-form');
  const fields = form.elements;
  const weights = [...form.querySelectorAll('[data-weight]')];
  const preset = get('work-preset');
  const run = get('work-run');
  const status = get('work-status');
  const result = get('work-result');
  const amount = new Intl.NumberFormat('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
  const percent = n => (Number(n)*100).toFixed(2)+'%';
  const buttons = [...document.querySelectorAll('[data-view]')];
  let chart, series, response, view = 'drawdown', generation = 0, controller, downloadUrl;
  function parameters() {
    return new URLSearchParams({start:fields.start.value,end:fields.end.value,capital:fields.capital.value,
      weights:weights.map(input=>input.value).join(','),rebalance:fields.rebalance.value,fees:fields.fees.value});
  }
  function mix() {
    const values = weights.map(input=>Number(input.value));
    const total = values.reduce((a,b)=>a+b,0);
    get('work-mix').textContent = total > 0 && values.every(n=>Number.isFinite(n) && n>=0)
      ? '折算仓位（按上方顺序） '+values.map(n=>percent(n/total)).join(' / ') : '请给至少一只 ETF 填写正数。';
    weights[0].setCustomValidity(total > 0 ? '' : '目标配比合计须大于零。');
    const raw = weights.map(i=>i.value).join(',');
    preset.value = [...preset.options].some(o=>o.value===raw) ? raw : '';
  }
  function changed() {
    generation++;
    controller?.abort();
    run.disabled = false;
    result.hidden = true;
    status.textContent = '参数已修改，点击运行查看结果。';
    mix();
  }
  form.addEventListener('input', event=>{if (event.target !== preset) changed();});
  preset.addEventListener('change', () => {
    if (!preset.value) { weights[0].focus(); weights[0].select(); return; }
    preset.value.split(',').forEach((v,i)=>weights[i].value=v);
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
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    const token = ++generation;
    controller?.abort();
    controller = new AbortController();
    run.disabled = true;
    result.hidden = true;
    status.textContent = '正在按所选参数从现金起步回放…';
    const params = parameters(), url = 'api/v1/backtest?'+params.toString();
    try {
      const res = await fetch(url,{signal:controller.signal});
      const data = await res.json();
      if (!res.ok) throw Error(data.error || '服务暂时不可用。');
      if (token !== generation) return;
      display(data,params,url);
      status.textContent = '回测完成。';
    } catch (err) {
      if (token === generation) {result.hidden = true;status.textContent = '运行失败。'+err.message;}
    } finally {if (token === generation) run.disabled = false;}
  });
  async function setup() {
    try {
      const res = await fetch('api/v1/backtest/options');
      if (!res.ok) throw Error();
      const config = await res.json(), query = new URLSearchParams(location.search);
      const params = Object.fromEntries(config.required.map(k=>[k,query.get(k) ?? config.defaults[k]]));
      for (const key of ['start','end','capital','fees','rebalance']) fields[key].value = params[key];
      for (const input of [fields.start,fields.end]) {input.min=config.first;input.max=config.last;}
      const parts = params.weights.split(',');
      weights.forEach((input,i)=>{input.min='0';input.max='99999.99';input.step='.01';input.value=parts[i] ?? '';});
      mix();
      get('work-limits').textContent = '可用日期 '+config.first+' 至 '+config.last+'。休市端点取区间内交易日。按场内人民币收盘价计入分红，起点后的首个开盘模拟建仓。';
      run.disabled = false;
      if (config.required.every(k=>query.has(k))) form.requestSubmit();
    } catch {status.textContent = '回测服务暂时不可用，请刷新重试。';}
  }
  setup();
})();
