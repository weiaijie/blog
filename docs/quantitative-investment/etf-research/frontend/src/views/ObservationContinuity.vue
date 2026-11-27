<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { getJson } from '../state';

type Slot={at:string; state:string};
type Source={status:string;readyAt:string|null};
type Day={
  day:string; cutoffAt:string|null; qualification:string; scheduledAttempts:number; manualAttempts:number;
  verifiedSlots:number; slots:Slot[]; sources:Record<string,Source>; archiveIssues:{id:string;status:string}[];
};
type Report={
  asOf:string; targetSessions:number; trackedSessions:number; completedWindows:number; collecting:boolean;
  calendarUnknownYear:number|null; daysWithScheduledArchive:number; daysWithVerifiedTimer:number;
  qualifiedOnTime:number; days:Day[];
};
const endpoint='/api/v1/research/observation/continuity';
const report=ref<Report>();
const error=ref('');
const request=new AbortController();
const states:Record<string,string>={
  on_time:'按时合格', qualified_late:'迟到后合格', awaiting_cutoff:'等待截止',
  cutoff_unknown:'截止待核验', incomplete:'截止时数据未齐', no_scheduled_archive:'截止时无定时归档',
};
const slots:Record<string,string>={
  verified:'已核验定时时点', unconfirmed_clock:'归档存在，触发时点未核实',
  upcoming:'尚未到时', awaiting_archive:'等待归档', not_verified:'未见该时点的核验归档',
};
const sources:Record<string,string>={
  policy:'官方政策', '510300':'510300 份额净值', '511010':'511010 份额净值', turnover:'沪市成交额', margin:'沪市两融',
};
const labels:Record<string,string>={
  on_time:'已按时取得', late:'截止后取得', missing:'尚缺证据', cutoff_unknown:'已取得，截止待核验',
};
const time=(value:string)=>new Date(value).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false});
onMounted(async()=>{
  try { report.value=await getJson<Report>(endpoint,request.signal); }
  catch(reason){ if(!request.signal.aborted) error.value=(reason as Error).message; }
});
onBeforeUnmount(()=>request.abort());
</script>

<template>
  <section class="continuity" aria-labelledby="continuity-title">
    <div class="continuity-head">
      <h3 id="continuity-title">首 20 个应采交易日</h3>
      <a :href="endpoint" target="_blank" rel="noopener">连续性 JSON ↗</a>
    </div>
    <p v-if="error" role="alert">{{error}}</p>
    <p v-else-if="!report" role="status">正在核对采集回执…</p>
    <template v-if="report">
      <p>已跟踪 {{report.trackedSessions}} / {{report.targetSessions}} 日 · 已过截止 {{report.completedWindows}} 日 · 按时合格 {{report.qualifiedOnTime}} 日</p>
      <p class="muted">有定时归档 {{report.daysWithScheduledArchive}} 日 · 定时时点已核验 {{report.daysWithVerifiedTimer}} 日 · 以次一交易日 08:55 为截止</p>
      <p v-if="report.calendarUnknownYear" class="muted">{{report.calendarUnknownYear}} 年交易日历待核验。</p>
      <details v-for="row in report.days" :key="row.day">
        <summary>{{row.day}} · {{states[row.qualification] ?? row.qualification}}</summary>
        <p class="muted">{{row.scheduledAttempts}} 次定时归档 · {{row.manualAttempts}} 次手工归档
          <template v-if="row.cutoffAt"> · 截止 {{time(row.cutoffAt)}}</template>
          <template v-if="row.archiveIssues.length"> · {{row.archiveIssues.length}} 份归档有待核验</template>
        </p>
        <div class="continuity-grids">
          <ul aria-label="来源就绪">
            <li v-for="(part,key) in row.sources" :key="key">{{sources[key] ?? key}} · {{labels[part.status] ?? part.status}}
              <small v-if="part.readyAt">{{time(part.readyAt)}}</small></li>
          </ul>
          <ul aria-label="定时时点核验">
            <li v-for="slot in row.slots" :key="slot.at">{{time(slot.at)}} · {{slots[slot.state] ?? slot.state}}</li>
          </ul>
        </div>
      </details>
    </template>
  </section>
</template>

<style scoped>
.continuity{border-top:1px solid #d8e2e8;margin-top:18px;padding-top:14px}
.continuity-head{display:flex;align-items:center;justify-content:space-between;gap:6px 16px;flex-wrap:wrap}
.continuity-head h3{margin:0}
.continuity p{margin:8px 0}
.continuity summary{cursor:pointer;padding:7px 0;font-weight:600}
.continuity-grids{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,275px),1fr));gap:10px 18px}
.continuity-grids ul{margin:0 0 10px;padding-inline-start:20px}
.continuity-grids li{margin:4px 0}
.continuity-grids small{color:#526b7b;margin-inline-start:6px}
</style>
