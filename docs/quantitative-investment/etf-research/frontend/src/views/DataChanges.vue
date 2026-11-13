<script setup lang="ts">
import {ref,computed,onMounted,onBeforeUnmount,watch} from 'vue';
import {getJson,download} from '../state';
import {money,pct,apiUrl,type Decimal,type Replay,type Point,type Attribution,type Gap} from '../domain';
import Chart from '../components/Chart.vue';import DayDetail from '../components/DayDetail.vue';import AttributionTable from '../components/AttributionTable.vue';
interface Metrics{count:number;profitable:number;reached:number;worstPnl:Decimal;profitRate:Decimal;targetRate:Decimal;worstStart:string;worstEnd:string;worstCase:string}
interface NewWindow{start:string;end:string;pnl:Decimal;annualized_return:Decimal;case:string;haltEffectPnl:Decimal;blockedOrders:number}
interface Period{before:Metrics;after:Metrics;delta:Metrics;sampleEffect:Metrics;haltEffect:Metrics;addedMaturities:number;oldMaturitiesUnchanged:number;haltChangedWindows:number;newWindows:NewWindow[]}
interface Scenario{id:string;label:string;group:string;start:string;periods:Record<string,Period>;newHaltBlockedOrders:number}
interface Report{oldThrough:string;newThrough:string;newSessions:string[];capital:string;openingHalts:string[];scenarios:Scenario[];controlCase:string;notes:string[]}
interface Detail{case:{start:string;end:string;kind:string};scenario:{label:string};actual:Replay;counterfactual:null|{effect:Decimal;curve:Point[];orders:unknown[];contribution:Attribution;dailyGap:Gap;assumption:string}}
const endpoint='/api/v2/backtest/data-change';const report=ref<Report>(),group=ref('domestic'),year=ref('1'),selected=ref(''),detail=ref<Detail>(),day=ref(''),detailUrl=ref(''),error=ref(''),busy=ref(false);
let controller:AbortController|undefined,generation=0;
const rows=computed(()=>report.value?.scenarios.filter(s=>s.group===group.value)||[]);
const scenario=computed(()=>rows.value.find(s=>s.id===selected.value));const period=computed(()=>scenario.value?.periods[year.value]);
function clear(){generation++;controller?.abort();detail.value=undefined;detailUrl.value='';busy.value=false;error.value='';}
watch([group,year],()=>{clear();selected.value=rows.value[0]?.id||'';});onBeforeUnmount(clear);
async function load(){clear();const run=generation;controller=new AbortController();busy.value=true;try{const data=await getJson<Report>(endpoint,controller.signal);if(run!==generation)return;report.value=data;selected.value=data.scenarios[0]!.id;}catch(e){if(run===generation)error.value=(e as Error).message;}finally{if(run===generation)busy.value=false;}}
onMounted(load);
function select(id:string){clear();selected.value=id;}
async function openCase(id:string){clear();const run=generation;controller=new AbortController();busy.value=true;try{const url=apiUrl(endpoint+'-detail',{case:id}),data=await getJson<Detail>(url,controller.signal);if(run!==generation)return;detail.value=data;detailUrl.value=url;day.value=data.actual.frames.find(f=>f.orders.some(o=>o.reason==='opening_halt'))?.date||data.actual.frames.at(-1)!.date;}catch(e){if(run===generation)error.value=(e as Error).message;}finally{if(run===generation)busy.value=false;}}
const frames=computed(()=>detail.value?.actual.frames||[]);const frame=computed(()=>frames.value.find(f=>f.date===day.value));const previous=computed(()=>frames.value[frames.value.findIndex(f=>f.date===day.value)-1]);
const gapDay=computed(()=>detail.value?.counterfactual?.dailyGap.days.find(r=>r.date===day.value));
const lines=computed(()=>{
 const curves:Array<{label:string;color:string;points:Point[]}>=[{label:'按公告限制执行',color:'#237764',points:frames.value}];
 if(detail.value?.counterfactual)curves.push({label:'假设忽略新增停牌',color:'#b66632',points:detail.value.counterfactual.curve});
 return curves.flatMap(c=>[{label:c.label+' 权益',color:c.color,pane:0,points:c.points.map(p=>({date:p.date,value:+p.equity}))},{label:c.label+' 回撤%',color:c.color,pane:1,points:c.points.map(p=>({date:p.date,value:100*+p.drawdown}))}]);
});
const signed=(x:Decimal)=>Number(x)>0?'+'+money(x):money(x);
const countDelta=(x:number)=>x>0?'+'+x:String(x);
</script>
<template>
 <div class="page-title"><div><h1>新增9天，结果改变了什么</h1><p>10月30日原样本 → 11月12日近期样本。固定10万元、基准费用；本页不受右上角草稿方案控制。</p></div><el-button v-if="report" @click="download('etf-data-version-comparison.json',report)">导出对比</el-button></div>
 <el-alert v-if="error" :title="error" type="error" :closable="false"/><p v-if="busy" role="status">正在核对账目与交易记录…</p><el-button v-if="!report&&!busy" @click="load">重新加载</el-button>
 <template v-if="report">
 <section class="panel"><h2>先分清两种变化</h2><p>旧窗口的到期日与结果保持不变。每种模型各新增9个一年窗口、9个两年窗口；总次数增加不等于胜率提高。</p><p>七个境内模型不持有标普。四组跨市场基准在新增5个停牌日没有计划开盘交易，因此这些满期统计的停牌规则影响为0。下方提供未满一年的对照案例，核验停牌拦单确实生效。</p><a :href="endpoint" target="_blank" rel="noopener">Agent：版本对比JSON</a></section>
 <section class="panel"><div class="actions"><label>比较范围<select v-model="group"><option value="domestic">七种境内模型 · 2019-03-20起</option><option value="markets">四组跨市场基准 · 2022-03-30起</option></select></label><label>持有期限<select v-model="year"><option value="1">1年</option><option value="2">2年</option></select></label></div>
 <p class="muted">{{group==='domestic'?'沪深300与国债：一次建仓、分三批建仓后持有；趋势/因子按原规则交易。':'四组均股债50/50，按月再平衡；三市场组将股票仓位等分。为避开标普拆分断点，起点为2022-03-30。'}} 两个范围的起点不同，不直接比较总次数。</p>
 <div class="table-scroll" tabindex="0"><table class="change-table"><thead><tr><th>模型 / 组合</th><th>满期次数<br>旧 → 新（变化）</th><th>赚钱次数<br>旧 → 新（变化）</th><th>年化≥4%次数<br>旧 → 新（变化）</th><th>最差盈亏（元）<br>旧 → 新（变化）</th><th>停牌规则影响<br>赚钱 / 达标 / 最差</th></tr></thead><tbody><tr v-for="s in rows" :key="s.id"><th><button class="text-button" :aria-pressed="selected===s.id" @click="select(s.id)">{{s.label}}</button></th><td>{{s.periods[year]!.before.count}} → {{s.periods[year]!.after.count}}<br>（{{countDelta(s.periods[year]!.delta.count)}}）</td><td>{{s.periods[year]!.before.profitable}} → {{s.periods[year]!.after.profitable}}<br>（{{countDelta(s.periods[year]!.delta.profitable)}}）<br><small>{{pct(s.periods[year]!.before.profitRate)}} → {{pct(s.periods[year]!.after.profitRate)}}</small></td><td>{{s.periods[year]!.before.reached}} → {{s.periods[year]!.after.reached}}<br>（{{countDelta(s.periods[year]!.delta.reached)}}）<br><small>{{pct(s.periods[year]!.before.targetRate)}} → {{pct(s.periods[year]!.after.targetRate)}}</small></td><td>{{money(s.periods[year]!.before.worstPnl)}} → {{money(s.periods[year]!.after.worstPnl)}}<br>（{{signed(s.periods[year]!.delta.worstPnl)}}）<br><small v-if="Number(s.periods[year]!.after.worstPnl)>0">最差一期仍盈利</small></td><td>{{countDelta(s.periods[year]!.haltEffect.profitable)}} / {{countDelta(s.periods[year]!.haltEffect.reached)}} / {{signed(s.periods[year]!.haltEffect.worstPnl)}}元</td></tr></tbody></table></div></section>
 <section v-if="scenario&&period" class="panel"><h2>{{scenario.label}} · 新到期的{{year}}年窗口</h2><p>旧有{{period.oldMaturitiesUnchanged}}期结果不变，新增{{period.addedMaturities}}期。赚钱次数变化={{countDelta(period.sampleEffect.profitable)}}（样本）+{{countDelta(period.haltEffect.profitable)}}（停牌规则）；达标次数同样为{{countDelta(period.sampleEffect.reached)}}+{{countDelta(period.haltEffect.reached)}}。</p>
 <div class="table-scroll" tabindex="0"><table class="new-window-table"><thead><tr><th>新到期窗口</th><th>净盈亏（元）</th><th>年化收益</th><th>新增停牌阻断订单</th><th>停牌条件差额（元）</th></tr></thead><tbody><tr v-for="w in period.newWindows" :key="w.case"><th><button class="text-button" :disabled="busy" @click="openCase(w.case)">{{w.start}} 至 {{w.end}}</button></th><td>{{money(w.pnl)}}</td><td>{{pct(w.annualized_return)}}</td><td>{{w.blockedOrders}}</td><td>{{signed(w.haltEffectPnl)}}</td></tr></tbody></table></div>
 <div class="actions"><el-button :disabled="busy" @click="openCase(period.before.worstCase)">打开旧最差一期</el-button><el-button :disabled="busy" @click="openCase(period.after.worstCase)">打开新最差一期</el-button></div><p class="muted">旧最差：{{period.before.worstStart}} 至 {{period.before.worstEnd}}；新最差：{{period.after.worstStart}} 至 {{period.after.worstEnd}}。最小值可能对应不同账户，差额不解释为同一账户追加9天盈亏。</p></section>
 <section class="panel"><h2>停牌会拦单，但不一定改变这批满期统计</h2><p>标普新增开盘停牌日：{{report.openingHalts.join('、')}}。打开11月2日开始的一次建仓案例，比较11月3日按公告拒绝买入，与假设套用日线开盘价成交的账目。</p><el-button :disabled="busy" @click="openCase(report.controlCase)">查看停牌拦单对照（未满一年）</el-button><p class="muted">该案例不计入一年/两年统计。假设价格可能是复牌后首笔价，无停牌时真实可成交价格未知；条件差额不代表真实机会损失。</p></section>
 <section v-if="detail" class="panel"><div class="section-head"><h2>{{detail.scenario.label}} · 区间核对</h2><a :href="detailUrl" target="_blank" rel="noopener">Agent：区间明细JSON</a></div><p>{{detail.case.start}} 至 {{detail.case.end}}，{{detail.actual.parameters.capital}}元。{{detail.case.kind==='diagnostic'?'仅短区间规则诊断，不是满期成绩。':''}}</p>
 <p v-if="detail.counterfactual">按公告执行 减 假设忽略新增停牌：{{signed(detail.counterfactual.effect)}}元。{{detail.counterfactual.assumption}}</p>
 <Chart :lines="lines" :height="440" label="同区间权益（元）与回撤（%）；假设曲线仅用于规则敏感性诊断" @select="date=>day=date"/>
 <label>核对交易日<select v-model="day"><option v-for="f in frames" :key="f.date">{{f.date}}</option></select></label>
 <DayDetail v-if="frame" :frame="frame" :previous="previous"/>
 <template v-if="detail.counterfactual"><h3>整个区间的条件差额</h3><AttributionTable :data="detail.counterfactual.contribution"/><h3>{{day}} 当日条件差额 {{signed(gapDay?.change||0)}}元</h3><AttributionTable v-if="gapDay" :data="gapDay"/></template>
 </section>
 <section class="panel"><h2>核对口径</h2><ul><li v-for="note in report.notes" :key="note">{{note}}</li></ul></section>
 </template>
</template>
