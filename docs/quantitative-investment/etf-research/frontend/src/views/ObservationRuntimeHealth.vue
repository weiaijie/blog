<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { getJson } from '../state';

type Job = {state:string;lastTriggerAt:string|null;finishedAt:string|null;nextAt:string|null};
type RuntimeHealth = {state:string;checkedAt:string|null;issues:string[];jobs:Record<string,Job>};
const endpoint='/api/v1/research/observation/runtime-health';
const names:Record<string,string>={
  'calendar-watch':'交易日历巡检',observation:'来源采集',model:'分折训练',decision:'盘前封存',forecast:'预测封存',opening:'开盘取证',
  label:'五日标签',evaluation:'样本外评估','monthly-coverage':'月度覆盖','observation-export':'夜间证据导出',
};
const states:Record<string,string>={
  current:'记录可查',attention:'有待核对任务',stale:'观察已过期',waiting:'等待运行',
  completed:'已完成',late_trigger:'补跑或触发迟到',running:'执行中',stalled:'执行超时',
  failed:'执行失败',missed_schedule:'计划时点漏跑',timer_inactive:'定时器未启用',
  execution_unverified:'执行回执待核验',unit_unavailable:'服务状态未知',
  timer_configuration_mismatch:'定时配置待核对',
};
const report=ref<RuntimeHealth>();
const busy=ref(false);
const failure=ref('');
let pending:AbortController|undefined;
const time=(value:string|null)=>value ? value.slice(0,19).replace('T',' ') : '—';
async function load(){
  pending?.abort();
  const request=new AbortController();
  pending=request;
  busy.value=true;
  failure.value='';
  try {
    const snapshot=await getJson<RuntimeHealth>(endpoint,request.signal);
    if(!request.signal.aborted)report.value=snapshot;
  } catch(e) {
    if(!request.signal.aborted)failure.value=(e as Error).message;
  } finally {
    if(!request.signal.aborted)busy.value=false;
  }
}
onMounted(load);
onBeforeUnmount(()=>pending?.abort());
</script>

<template>
  <details class="panel runtime-health">
    <summary>独立研究运行健康<span v-if="report && !failure"> · {{states[report.state] ?? report.state}}</span></summary>
    <div class="runtime-head">
      <p v-if="report?.checkedAt && !failure">最近核查 {{time(report.checkedAt)}}（北京时间）</p>
      <a :href="endpoint" target="_blank" rel="noopener">Agent 同源 JSON ↗</a>
      <button type="button" :disabled="busy" @click="load">刷新</button>
    </div>
    <p v-if="failure" role="alert">{{failure}}</p>
    <p v-else-if="busy && !report" role="status">正在读取运行记录…</p>
    <p v-else-if="!report?.checkedAt">等待下一次健康核查。</p>
    <div v-else class="runtime-table" tabindex="0" aria-label="独立研究定时任务运行记录">
      <table>
        <thead><tr><th scope="col">任务</th><th scope="col">状态</th><th scope="col">最近触发</th>
          <th scope="col">最近结束</th><th scope="col">下次触发</th></tr></thead>
        <tbody><tr v-for="(job,key) in report.jobs" :key="key">
          <th scope="row">{{names[key] ?? key}}</th><td>{{states[job.state] ?? job.state}}</td>
          <td>{{time(job.lastTriggerAt)}}</td><td>{{time(job.finishedAt)}}</td><td>{{time(job.nextAt)}}</td>
        </tr></tbody>
      </table>
    </div>
  </details>
</template>

<style scoped>
summary{cursor:pointer;font-weight:600}
.runtime-head{display:flex;align-items:center;gap:8px 16px;flex-wrap:wrap;margin:8px 0}
.runtime-head p{margin:0}
.runtime-table{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
th,td{text-align:left;padding:7px;white-space:nowrap;border-bottom:1px solid #d8e2e8}
</style>
