<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { apiUrl } from '../domain';
import { getJson } from '../state';

type Gap = {start:string;end:string;sessions:number};
type Source = {available:number;onTime:number;late:number;cutoffUnknown:number;missing:number;gaps:Gap[]};
type Response = {
  report:{month:string;asOf:string;state:string;sealAfter:string|null;calendarUnknownYear:number|null;
    expected:number;archived:number;qualified:number;noScheduledArchive:number;qualificationGaps:Gap[];
    sources:Record<string,Source>};
  archive:{state:string;archiveSha256:string|null;verifiedAt:string|null;issues:{unverified:number;pending:number}};
};

const endpoint = '/api/v1/research/observation/monthly';
const month = ref(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit'})
  .formatToParts().filter(part=>part.type==='year'||part.type==='month').map(part=>part.value).join('-'));
const currentMonth = month.value;
const response = ref<Response>();
const error = ref('');
const busy = ref(false);
const names:Record<string,string> = {
  policy:'官方政策原文', '510300':'510300 份额净值', '511010':'511010 份额净值', turnover:'沪市成交额', margin:'沪市两融',
};
const states:Record<string,string> = {
  open:'月度进度', ready_to_archive:'等待月度封存', calendar_unverified:'交易日历待核验', before_launch:'独立采集启动前',
};

let request:AbortController|undefined;
const time = (value:string) => new Date(value).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false});
const span = (gap:Gap) => (gap.start===gap.end ? gap.start : gap.start+' 至 '+gap.end)+' · '+gap.sessions+' 个交易日';

async function load() {
  request?.abort();
  const next = new AbortController();
  request = next;
  busy.value = true;
  error.value = '';
  try {
    response.value = await getJson<Response>(apiUrl(endpoint,{month:month.value}),next.signal);
  } catch (reason) {
    if (!next.signal.aborted) error.value = (reason as Error).message;
  } finally {
    if (!next.signal.aborted) busy.value = false;
  }
}

onMounted(load);
onBeforeUnmount(()=>request?.abort());
</script>

<template>
  <section class="month" aria-labelledby="monthly-coverage-title">
    <div class="month-head">
      <h3 id="monthly-coverage-title">月度数据覆盖</h3>
      <form @submit.prevent="load">
        <label for="coverage-month">月份</label>
        <input id="coverage-month" v-model="month" type="month" pattern="[0-9]{4}-[0-9]{2}" :max="currentMonth" required>
        <button type="submit" :disabled="busy">查询</button>
      </form>
    </div>
    <p v-if="busy" role="status">正在核对月度回执…</p>
    <p v-if="error" role="alert">{{error}}</p>
    <template v-if="response">
      <div class="month-head">
        <p class="muted">{{response.report.month}} · {{response.archive.state==='verified' ? '已封存' :
          response.archive.state==='unverified' ? '月度归档未通过核验' : states[response.report.state]}}
          · {{time(response.report.asOf)}} 核对</p>
        <a :href="apiUrl(endpoint,{month:response.report.month})" target="_blank" rel="noopener">查看月度 JSON ↗</a>
      </div>
      <p v-if="response.report.calendarUnknownYear" class="muted">{{response.report.calendarUnknownYear}} 年交易日历待核验。</p>
      <p v-if="response.archive.verifiedAt" class="muted">归档核验 {{time(response.archive.verifiedAt)}}</p>
      <p v-if="response.archive.issues.pending || response.archive.issues.unverified" class="muted">
        {{response.archive.issues.pending}} 份归档未完成 · {{response.archive.issues.unverified}} 份未通过校验。
      </p>
      <template v-if="response.report.expected">
        <p>{{response.report.expected}} 个应采交易日 · {{response.report.archived}} 日有定时归档 ·
          {{response.report.qualified}} 日合格</p>
        <div class="table-scroll" tabindex="0" aria-label="月度来源覆盖">
          <table class="compact monthly-table">
            <thead><tr><th>来源</th><th>证据齐备</th><th>按时</th><th>迟到</th><th>截止未知</th><th>缺证</th></tr></thead>
            <tbody><tr v-for="(item,key) in response.report.sources" :key="key">
              <th scope="row">{{names[key] ?? key}}</th><td>{{item.available}} / {{response.report.expected}}</td>
              <td>{{item.onTime}}</td><td>{{item.late}}</td><td>{{item.cutoffUnknown}}</td><td>{{item.missing}}</td>
            </tr></tbody>
          </table>
        </div>
        <p class="muted">按下一交易日 08:55 的归档就绪时点计迟到。政策统计原文采集覆盖。</p>
        <details>
          <summary>连续缺口</summary>
          <dl class="gap-list">
            <div><dt>合格归档</dt><dd v-if="!response.report.qualificationGaps.length">无缺口</dd>
              <dd v-for="gap in response.report.qualificationGaps" :key="gap.start">{{span(gap)}}</dd></div>
            <div v-for="(item,key) in response.report.sources" :key="key">
              <dt>{{names[key] ?? key}}</dt><dd v-if="!item.gaps.length">无缺口</dd>
              <dd v-for="gap in item.gaps" :key="gap.start">{{span(gap)}}</dd>
            </div>
          </dl>
        </details>
      </template>
      <p v-else>本月暂无已核实的应采交易日。</p>
    </template>
  </section>
</template>

<style scoped>
.month{border-top:1px solid #d8e2e8;padding-top:12px;margin:14px 0}
.month-head,.month-head form{display:flex;align-items:center;justify-content:space-between;gap:8px 14px;flex-wrap:wrap}
.month-head h3,.month-head p{margin:0}
.month-head form{justify-content:flex-start;margin:4px 0 8px}
.month-head input,.month-head button{font:inherit;min-height:36px;max-width:100%}
.monthly-table{min-width:550px;font-variant-numeric:tabular-nums}
details{margin:12px 0}
details summary{cursor:pointer}
.gap-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 14px}
.gap-list dt{font-weight:600}
.gap-list dd{margin:3px 0}
</style>
