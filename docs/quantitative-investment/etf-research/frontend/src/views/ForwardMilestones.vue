<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { apiUrl, money, pct } from '../domain';
import { getJson, market } from '../state';

type Account = {
  strategy:string; scenario:string; endingCny:string; netPnlCny:string;
  netReturn:number; netAnnualized:number|null; netReturnVsBond:number;
  maxCloseDrawdown:number; totalCostCny:string; commissionsCny:string; taxCny:string; slippageCny:string;
  recovery:{peakOn:string;troughOn:string;recoveredOn:string|null;peakToRecoverySessions:number|null;underwaterCloses:number}|null;
};
type Accounts = Record<string,Account>;
type Milestone = {
  months:number; anniversary:string; endSession:string|null; expectedEndSession?:string;
  state:string; accounts:Accounts|null;
  publication?:{availableAt:string;checkpointSha256:string;operation:string;operationManifestSha256:string};
};
type ForwardReport = {
  asOf:string; anchorOn:string; valuationSessions:number; returnIntervals:number;
  firstReturnSession:string|null; progress:Accounts; milestones:Milestone[];
  publication?:{availableAt:string;mode:string};
};

const endpoint='/api/v1/research/forward-milestones';
const milestoneStates:Record<string,string> = {
  accumulating:'观察中',complete:'已核验',calendar_unverified:'日历待核验',
  awaiting_valuation:'等待到期估值',awaiting_publication:'等待到期检查点发布',
  publication_unverified:'到期回执待核验',ledger_conflict:'到期账本有冲突',
};
const labels=[
  ['cash','现金'],['bond_hold','仅持国债 ETF'],['equity_hold','仅持沪深300 ETF'],
  ['monthly_20_80','月度股债 20/80'],['monthly_50_50','月度股债 50/50'],['trend_120','120 日趋势'],
] as const;
const report=ref<ForwardReport>();
const period=ref(0);
const fees=ref('base');
const error=ref('');
const busy=ref(false);
const timeInput=ref('');
const selectedTime=ref('');
const requestUrl=computed(()=>selectedTime.value?apiUrl(endpoint,{asOf:selectedTime.value}):endpoint);
let pending:AbortController|undefined;

async function load(){
  pending?.abort();
  const request=new AbortController();
  pending=request;
  busy.value=true;
  error.value='';
  report.value=undefined;
  try {
    const loaded=await getJson<ForwardReport>(requestUrl.value,request.signal);
    if(!request.signal.aborted)report.value=loaded;
  }
  catch(e){ if(!request.signal.aborted) error.value=(e as Error).message; }
  finally { if(!request.signal.aborted) busy.value=false; }
}
function showHistorical(){
  const clock=timeInput.value;
  if(!clock)return;
  selectedTime.value=(clock.length===16?clock+':00':clock)+'+08:00';
  void load();
}
function showLatest(){
  timeInput.value='';
  selectedTime.value='';
  void load();
}
watch(()=>market.value?.asOf,()=>{if(!selectedTime.value)void load();},{immediate:true});
onBeforeUnmount(()=>pending?.abort());
const milestone=computed(()=>report.value?.milestones.find(row=>row.months===period.value));
const selected=computed(()=>period.value===0?report.value?.progress:milestone.value?.accounts);
const rows=computed(()=>selected.value?labels.map(([key,label])=>({label,...selected.value![key+'_'+fees.value]})):[]);
</script>

<template>
  <section class="panel" aria-label="18 户前瞻模拟">
    <div class="forward-head">
      <div><h2>18 户前瞻模拟</h2><p v-if="report">
        截至 {{report.asOf}} · {{report.valuationSessions}} 个收盘估值日 · {{report.returnIntervals}} 个收益区间
      </p></div>
      <a :href="requestUrl" target="_blank" rel="noopener">Agent 同源 JSON ↗</a>
    </div>
    <form class="forward-filters" @submit.prevent="showHistorical">
      <label for="forward-observed-time">按时点回看（北京时间）</label>
      <input id="forward-observed-time" v-model="timeInput" type="datetime-local" step="1" required>
      <button type="submit" :disabled="busy">查看</button>
      <button v-if="selectedTime" type="button" @click="showLatest">回到最新</button>
    </form>
    <p v-if="error" role="alert">{{error}} <button type="button" @click="load">重试</button></p>
    <p v-else-if="busy && !report" role="status">正在核对账户检查点…</p>
    <template v-if="report && !error">
      <p v-if="report.publication" class="muted">
        检查点发布于 {{report.publication.availableAt.slice(0,19).replace('T',' ')}}（北京时间）。
      </p>
      <p class="muted">{{report.anchorOn}} 为初始资金估值日。<template v-if="report.firstReturnSession">首个收益日是 {{report.firstReturnSession}}。</template></p>
      <dl class="forward-milestones">
        <div v-for="row in report.milestones" :key="row.months">
          <dt>{{row.months}} 个月</dt><dd>{{row.endSession ?? row.expectedEndSession ?? row.anniversary}}</dd>
          <small>{{milestoneStates[row.state] ?? row.state}}</small>
        </div>
      </dl>
      <div class="forward-filters">
        <label>统计区间 <select v-model.number="period"><option :value="0">累计</option>
          <option v-for="row in report.milestones" :key="row.months" :value="row.months">{{row.months}} 个月</option>
        </select></label>
        <label>费用情景 <select v-model="fees"><option value="base">基准</option><option value="low">低费用</option><option value="high">高费用</option></select></label>
      </div>
      <p v-if="!rows.length" role="status">
        {{milestone ? milestoneStates[milestone.state] ?? milestone.state : '账户数据待核验'}}
      </p>
      <div v-else class="forward-table" tabindex="0" aria-label="模拟账户指标">
        <table>
          <thead><tr><th scope="col">账户</th><th scope="col">净盈亏（元）</th><th scope="col">净收益</th>
            <th scope="col">净年化</th><th scope="col">最大回撤</th><th scope="col">恢复前高</th><th scope="col">成本（元）</th></tr></thead>
          <tbody><tr v-for="row in rows" :key="row.strategy">
            <th scope="row">{{row.label}}</th><td>{{money(row.netPnlCny)}}</td><td>{{pct(row.netReturn)}}</td>
            <td>{{pct(row.netAnnualized)}}</td><td>{{pct(row.maxCloseDrawdown)}}</td>
            <td v-if="row.recovery">{{row.recovery.recoveredOn ?? '期末未恢复'}}<small v-if="row.recovery.peakToRecoverySessions!==null">
              {{row.recovery.peakToRecoverySessions}} 个交易日</small></td>
            <td v-else>无回撤</td>
            <td>{{money(row.totalCostCny)}}<small>佣金 {{money(row.commissionsCny)}} · 滑点 {{money(row.slippageCny)}} · 税 {{money(row.taxCny)}}</small></td>
          </tr></tbody>
        </table>
      </div>
      <details v-if="milestone?.publication" class="milestone-proof">
        <summary>到期检查点与发布回执</summary>
        <p>首次发布 {{milestone.publication.availableAt.slice(0,19).replace('T',' ')}}（北京时间）</p>
        <p>检查点 <code>{{milestone.publication.checkpointSha256}}</code></p>
        <p>回执 <code>{{milestone.publication.operationManifestSha256}}</code></p>
      </details>
      <p class="muted">净年化仅在 12、24 个月期满时计算。期末权益按收盘估值，未计强制平仓成本。</p>
    </template>
  </section>
</template>

<style scoped>
.forward-head,.forward-filters{display:flex;flex-wrap:wrap;gap:10px 20px;align-items:center}
.forward-head{justify-content:space-between}
.forward-head h2,.forward-head p{margin:0}
.milestone-proof code{overflow-wrap:anywhere}
.forward-head p{margin-top:6px}
.forward-milestones{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:14px 0}
.forward-milestones div{background:#f2f6f7;padding:8px}
.forward-milestones dd{margin:4px 0;overflow-wrap:anywhere;font-variant-numeric:tabular-nums}
.forward-filters{margin:12px 0}
.forward-filters select,.forward-filters input{padding:4px;background:white;color:#23344a;border:1px solid #a4b6c1;border-radius:4px}
.forward-filters select{margin-inline-start:5px}
.forward-filters input{max-width:100%}
.forward-table{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
td,th{padding:8px;text-align:left;white-space:nowrap;border-bottom:1px solid #d8e2e8}
td small{display:block;color:#526b7b;font-size:12px}
</style>
