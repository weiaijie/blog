<script setup lang="ts">
import {ref,computed,onMounted,onBeforeUnmount} from 'vue';
import {getJson,download} from '../state';
import {money,pct,apiUrl,type Decimal,type Replay,type Attribution,type Gap} from '../domain';
import Chart from '../components/Chart.vue';import DayDetail from '../components/DayDetail.vue';import AttributionTable from '../components/AttributionTable.vue';
type Model='allocation'|'multifactor_v1';
interface Metric{pnl:Decimal;annualized_return:Decimal;reached:boolean;targetGap:Decimal;cost:Decimal;fixedFillGrossPnl:Decimal;fixedFillGrossReached:boolean;filledOrders:number;attribution:Attribution}
interface Window{start:string;end:string;thresholdPnl:Decimal;metrics:Record<Model,Metric>;difference:Attribution&{accountChange:Decimal};regime:{parts:Record<string,Record<string,{price:Decimal;dividend:Decimal}>>;bondOnlyClosingSessions:number;totalSessions:number}}
interface Report{windows:Window[];notes:string[];counts:Record<Model,{profitable:number;reached:number;fixedFillGrossReached:number}>}
interface Detail extends Window{replays:Record<Model,Replay>;dailyGap:Gap}
const endpoint='/api/v2/backtest/new-window-attribution';
const report=ref<Report>(),detail=ref<Detail>(),error=ref(''),busy=ref(false),day=ref(''),url=ref('');
const models:Model[]=['allocation','multifactor_v1'];const labels={allocation:'一次建仓',multifactor_v1:'多因子'};
let controller:AbortController|undefined,generation=0;
function cancel(){generation++;controller?.abort();busy.value=false;}
onBeforeUnmount(cancel);
async function load(){cancel();const n=generation;controller=new AbortController();busy.value=true;error.value='';try{const r=await getJson<Report>(endpoint,controller.signal);if(n!==generation)return;report.value=r;}catch(e){if(n===generation)error.value=(e as Error).message;}finally{if(n===generation)busy.value=false;}}
async function open(start:string){cancel();const n=generation;controller=new AbortController();busy.value=true;error.value='';detail.value=undefined;url.value='';try{const u=apiUrl(endpoint+'-detail',{case:start}),r=await getJson<Detail>(u,controller.signal);if(n!==generation)return;detail.value=r;url.value=u;day.value=r.dailyGap.decreases[0]||r.end;}catch(e){if(n===generation)error.value=(e as Error).message;}finally{if(n===generation)busy.value=false;}}
onMounted(load);
function domestic(a:Attribution):Attribution{return {...a,byEtf:{'510300':a.byEtf['510300']!,'511010':a.byEtf['511010']!}};}
const signed=(v:Decimal)=>+v>0?'+'+money(v):money(v);
const gap=computed(()=>detail.value?.dailyGap.days.find(x=>x.date===day.value));
function frame(m:Model,offset=0){const f=detail.value?.replays[m].frames||[];return f[f.findIndex(x=>x.date===day.value)+offset];}
const lines=computed(()=>detail.value?models.flatMap((m,i)=>{const color=i?'#237764':'#b66632',frames=detail.value!.replays[m].frames;return [{label:labels[m]+' 权益',color,pane:0,points:frames.map(f=>({date:f.date,value:+f.equity}))},{label:labels[m]+' 回撤%',color,pane:1,points:frames.map(f=>({date:f.date,value:100*+f.drawdown}))}];}):[]);
const gapLines=computed(()=>[{label:'多因子 − 一次建仓（元）',color:'#526ca0',points:detail.value?.dailyGap.days.map(d=>({date:d.date,value:+d.cumulative}))||[]}]);
const regimeTotal=(w:Window,state:string,symbol:string)=>Number(w.regime.parts[state]?.[symbol]?.price||0)+Number(w.regime.parts[state]?.[symbol]?.dividend||0);
</script>
<template>
 <div class="page-title"><div><h1>9个新增两年窗口：收益差在哪里</h1><p>固定10万元、基准费用、截至2026-11-12的数据。下表不受草稿方案设置控制。</p><RouterLink to="/changes">← 返回新旧数据对比</RouterLink></div><el-button v-if="report" @click="download('etf-nine-window-attribution.json',report)">导出九期归因</el-button></div>
 <el-alert v-if="error" :title="error" type="error" :closable="false"/><p v-if="busy" role="status">正在加载逐日账目…</p><el-button v-if="!report&&!busy" @click="load">重新加载</el-button>
 <template v-if="report">
 <section class="panel"><h2>先看达标，再看原因</h2><p>多因子 {{report.counts.multifactor_v1.profitable}}/9 赚钱、{{report.counts.multifactor_v1.reached}}/9 年化达到4%；一次建仓 {{report.counts.allocation.profitable}}/9 赚钱、{{report.counts.allocation.reached}}/9 达标。加回账面佣金和滑点，多因子 {{report.counts.multifactor_v1.fixedFillGrossReached}}/9、一次建仓 {{report.counts.allocation.fixedFillGrossReached}}/9 达标。</p><p>这里的债仓是 <strong>511010 国债ETF，不是可转债</strong>。下方差额均为“多因子减一次建仓”，正数表示多因子多赚；价格、分红和成本逐项加总回到账户。</p><a :href="endpoint" target="_blank" rel="noopener">Agent：九期汇总JSON</a></section>
 <section class="panel"><h2>这批窗口说明了什么</h2><p>9期多因子均比一次建仓多赚，全债阶段少持股票与增加国债的净贡献均为正，额外换仓成本抵消了一部分优势。多因子6期未达标中，3期仅加回原成交账面的费用便跨过门槛，另外3期仍不足；一次建仓9期加回费用也都不够。</p><p class="muted">这只解释这9期历史结果，不表示全债切换在其他时期也有效，更不是调参建议。</p></section>
 <section class="panel"><h2>相同起点、相同终点逐一比较</h2><div class="table-scroll" tabindex="0"><table class="nine-table"><thead><tr><th>持有区间</th><th>一次建仓<br>盈亏 / 年化</th><th>多因子<br>盈亏 / 年化</th><th>多因子减一次建仓</th><th>沪深300<br>价格＋分红差</th><th>国债<br>价格＋分红差</th><th>额外佣金＋滑点贡献</th></tr></thead><tbody><tr v-for="w in report.windows" :key="w.start"><th><button class="text-button" :aria-pressed="detail?.start===w.start" :disabled="busy" @click="open(w.start)">{{w.start}} 至 {{w.end}}</button></th><td v-for="m in models" :key="m">{{money(w.metrics[m].pnl)}}元<br>{{pct(w.metrics[m].annualized_return)}} · {{w.metrics[m].reached?'达标':'未达标'}}</td><td>{{signed(w.difference.accountChange)}}元</td><td>{{signed(Number(w.difference.byEtf['510300']!.price)+Number(w.difference.byEtf['510300']!.dividend))}}</td><td>{{signed(Number(w.difference.byEtf['511010']!.price)+Number(w.difference.byEtf['511010']!.dividend))}}</td><td>{{signed(Number(w.difference.totals.commission)+Number(w.difference.totals.slippage))}}</td></tr></tbody></table></div><p class="muted">这9期高度重叠，不代表9个独立市场环境。点击区间查看两户账目、全债阶段和逐日买卖原因。</p></section>
 <section v-if="detail" class="panel"><div class="section-head"><h2>{{detail.start}} 至 {{detail.end}}</h2><a :href="url" target="_blank" rel="noopener">Agent：本期逐日明细JSON</a></div>
 <p>本期年化4%需要净赚 <strong>{{money(detail.thresholdPnl)}}元</strong>，按实际持有日数复利计算；净收益不足门槛为负差额。</p>
 <div class="table-scroll" tabindex="0"><table class="threshold-table"><thead><tr><th>模型</th><th>净盈亏</th><th>距4%门槛</th><th>佣金＋滑点成本</th><th>仅加回成本后</th><th>成交订单</th></tr></thead><tbody><tr v-for="m in models" :key="m"><th>{{labels[m]}}</th><td>{{money(detail.metrics[m].pnl)}}</td><td>{{signed(detail.metrics[m].targetGap)}}</td><td>{{money(detail.metrics[m].cost)}}</td><td>{{money(detail.metrics[m].fixedFillGrossPnl)}} · {{detail.metrics[m].fixedFillGrossReached?'达标':'仍未达标'}}</td><td>{{detail.metrics[m].filledOrders}}</td></tr></tbody></table></div>
 <h3>完整持有期的收益差额</h3><AttributionTable :data="domestic(detail.difference)"/>
 <details v-for="m in models" :key="m"><summary>{{labels[m]}}自身的股票、国债、分红和费用</summary><AttributionTable :data="domestic(detail.metrics[m].attribution)"/></details>
 <h3>转为全债期间，少持股票与增加国债各贡献多少</h3><p>多因子共{{detail.regime.bondOnlyClosingSessions}}个收盘全债状态 / {{detail.regime.totalSessions}}个观测日。以下是相对一次建仓的价格＋分红差，不含费用。</p>
 <div class="table-scroll" tabindex="0"><table class="regime-table"><thead><tr><th>多因子实际持仓状态</th><th>股票价格＋分红差</th><th>国债价格＋分红差</th><th>合计</th></tr></thead><tbody><tr v-for="state in ['bondOnly','other']" :key="state"><th>{{state==='bondOnly'?'全债阶段':'其余阶段（含未建仓）'}}</th><td>{{signed(regimeTotal(detail,state,'510300'))}}</td><td>{{signed(regimeTotal(detail,state,'511010'))}}</td><td>{{signed(regimeTotal(detail,state,'510300')+regimeTotal(detail,state,'511010'))}}</td></tr></tbody></table></div>
 <p class="muted">股票差为负：在该状态下，少持股票的价差及分红净贡献较差；为正则相反。国债差单列，两项相加才能评估该阶段的净作用。不能把事后账目解释为改变策略后必然可得的收益。</p>
 <Chart :lines="lines" :height="420" label="两种模型同区间账户权益与回撤" @select="d=>day=d"/>
 <Chart :lines="gapLines" :height="250" label="累计收益差额：多因子减一次建仓；点击日期查看原因" @select="d=>day=d"/>
 <div class="actions"><span>多因子相对改善最多：</span><button v-for="d in detail.dailyGap.increases" :key="d" class="text-button" @click="day=d">{{d}}</button></div>
 <div class="actions"><span>多因子相对恶化最多：</span><button v-for="d in detail.dailyGap.decreases" :key="d" class="text-button" @click="day=d">{{d}}</button></div>
 <label>核对交易日<select v-model="day"><option v-for="f in detail.replays.allocation.frames" :key="f.date">{{f.date}}</option></select></label>
 <h3>{{day}} · 当日差额 {{signed(gap?.change||0)}}元 / 累计 {{signed(gap?.cumulative||0)}}元</h3><AttributionTable v-if="gap" :data="domestic(gap)"/>
 <div class="table-scroll" tabindex="0"><table><thead><tr><th>ETF</th><th>前收</th><th>今日开盘</th><th>今日收盘</th></tr></thead><tbody><tr v-for="symbol in ['510300','511010']" :key="symbol"><th>{{symbol==='510300'?'沪深300':'国债'}} {{symbol}}</th><td>{{frame('allocation',-1)?.bars[symbol]?.close??'—'}}</td><td>{{frame('allocation')?.bars[symbol]?.open}}</td><td>{{frame('allocation')?.bars[symbol]?.close}}</td></tr></tbody></table></div>
 <details v-if="frame('multifactor_v1',-1)?.decision"><summary>查看前一日收盘因子（今日开盘只能使用此前信息）</summary><ul><li v-for="f in frame('multifactor_v1',-1)!.decision!.factors" :key="f.key">{{f.label}}：{{f.passed?'满足':'未满足'}} · {{pct(f.value)}}；{{f.rule}}</li></ul></details>
 <div v-for="m in models" :key="m"><h3>{{labels[m]}} · 持仓、因子和买卖</h3><DayDetail v-if="frame(m)" :frame="frame(m)!" :previous="frame(m,-1)"/></div>
 </section>
 <section class="panel"><h2>计算口径</h2><ul><li v-for="note in report.notes" :key="note">{{note}}</li></ul></section>
 </template>
</template>
