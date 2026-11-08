'use strict';
const groups = {
  '510300': ['沪深300', '#23705f'], '513500': ['标普500', '#b0552f'],
  '159920': ['恒生指数', '#406caf'], equal: ['三地平分', '#845391'],
  monthly_50_50: ['股债 50/50', '#23705f'], monthly_20_80: ['股债 20/80', '#845391'],
  equity_hold: ['持有沪深300', '#b0552f'], bond_hold: ['持有国债 ETF', '#406caf'],
  trend_120: ['120 日趋势', '#86671b'], cash: ['现金', '#67737a']
};
const order = ['510300','513500','159920','equal','monthly_50_50','monthly_20_80','equity_hold','bond_hold','trend_120','cash'];
const byId = id => document.getElementById(id);
const money = new Intl.NumberFormat('zh-CN', {minimumFractionDigits:2,maximumFractionDigits:2});
const pct = new Intl.NumberFormat('zh-CN', {style:'percent',minimumFractionDigits:2,maximumFractionDigits:2});
let data, chart, series = [], selected = '2';

function render() {
  const {dates, accounts} = data[selected];
  const full = selected === 'full';
  byId('bt-title').textContent = full ? '境内六种策略' : '股债各半的四组组合';
  byId('bt-range').textContent = dates[0]+' 至 '+dates.at(-1)+' · '+dates.length.toLocaleString('zh-CN')+' 个交易日 · 收盘总资产（元）';
  byId('bt-method').textContent = full
    ? '标的是沪深300 ETF 和国债 ETF。完整区间对照现金、买入持有、按月调回目标的两组股债配置，以及使用此前 120 个收盘价的趋势策略。'
    : '每组将一半资金配置在国债 ETF，另一半配置在沪深300、标普500、恒生 ETF 中的一种，或由三者平分。按月用前一交易日收盘数据计算目标，在下一交易日开盘模拟执行。';
  byId('bt-rows').replaceChildren();
  for (const line of series) chart.removeSeries(line);
  series = [];
  for (const key of order.filter(key => key in accounts)) {
    const account = accounts[key], [label,color] = groups[key];
    const line = chart.addSeries(LightweightCharts.LineSeries, {color,lineWidth:2,priceLineVisible:false,lastValueVisible:false});
    line.setData(dates.map((time,i) => ({time,value:account.equity[i]})));
    series.push(line);
    const row = byId('bt-rows').insertRow();
    const heading = document.createElement('th');
    heading.scope = 'row';
    const swatch = document.createElement('i');
    swatch.className = 'swatch';
    swatch.style.background = color;
    heading.append(swatch,label);
    row.append(heading);
    const recovery = !account.drawdown ? '无回撤' : account.recovered ? account.sessionsToRecover+' 天 · '+account.recovered : '期末尚未恢复';
    for (const value of [money.format(account.equity.at(-1)),pct.format(account.total),pct.format(account.annual),pct.format(account.drawdown),recovery]) {
      row.insertCell().textContent = value;
    }
  }
  chart.timeScale().fitContent();
  document.querySelectorAll('[data-period]').forEach(b => b.setAttribute('aria-pressed',String(b.dataset.period === selected)));
}

async function init() {
  try {
    const response = await fetch('backtest-data.json');
    if (!response.ok) throw Error('Historical accounts unavailable');
    data = await response.json();
    chart = LightweightCharts.createChart(byId('bt-chart'), {
      autoSize:true, layout:{textColor:'#526b70',attributionLogo:false},
      grid:{vertLines:{color:'#f2f5f2'},horzLines:{color:'#e8eeeb'}},
      localization:{locale:'zh-CN',dateFormat:'yyyy-MM-dd',priceFormatter:v=>money.format(v)}
    });
    render();
    document.querySelectorAll('[data-period]').forEach(b => b.addEventListener('click',() => {
      selected = b.dataset.period;
      render();
    }));
  } catch {
    byId('bt-range').textContent = '历史回测载入失败，请刷新重试。';
  }
}
async function initEntryWindows() {
  try {
    const response = await fetch('entry-windows.json');
    if (!response.ok) throw Error('Entry results unavailable');
    const report = await response.json();
    const buttons = document.querySelectorAll('[data-years]');
    function show(years) {
      const period = report.periods[years];
      const rows = byId('entry-rows');
      rows.replaceChildren();
      byId('entry-range').textContent = '可用起点 '+period.firstStart+' 至 '+period.lastStart+'，只计截至 '+report.lastSession+' 已满期的窗口。';
      for (const key of order.filter(key => key in period.groups)) {
        const result = period.groups[key];
        const row = rows.insertRow();
        const heading = document.createElement('th');
        heading.scope = 'row';
        heading.textContent = groups[key][0];
        row.append(heading);
        for (const n of [result.profitable, result.reached]) {
          row.insertCell().textContent = n+' / '+result.count+'（'+pct.format(n/result.count)+'）';
        }
        const sign = result.worstPnl > 0 ? '+' : '';
        row.insertCell().textContent = sign+money.format(result.worstPnl)+' 元（'+sign+pct.format(result.worstReturn)+'）';
        row.insertCell().textContent = result.worstStart+' 至 '+result.worstEnd+
          (result.worstTies > 1 ? '（并列 '+result.worstTies+' 次，列最早一期）' : '');
      }
      buttons.forEach(b=>b.setAttribute('aria-pressed', String(b.dataset.years === years)));
    }
    show('1');
    buttons.forEach(b=>b.addEventListener('click',()=>show(b.dataset.years)));
  } catch {
    byId('entry-range').textContent = '逐日起点结果载入失败，请刷新重试。';
  }
}

initEntryWindows();
init();
