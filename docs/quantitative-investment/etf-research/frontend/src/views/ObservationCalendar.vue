<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { apiUrl } from '../domain';
import { getJson } from '../state';

type Source = {status:string; httpStatus:number; receivedAt:string; candidates:{url:string;title:string}[]};
type Check = {status:string; checkedAt:string; sources:Record<string,Source>; archiveVerifiedAt?:string};
type CalendarReport = {
  year:number; admissionState:string; admission:{admittedAt:string|null}|null;
  latestScheduled:Check|null; latestManual:Check|null;
  scheduledIssues:{attempt:string;state:string;startedAt:string}[];
};
const endpoint = '/api/v1/research/observation/calendar-watch';
const result = ref<CalendarReport>();
const error = ref('');
const request = new AbortController();
const exchange:Record<string,string> = {sse:'上交所',szse:'深交所'};
const sourceStatus:Record<string,string> = {
  not_listed:'未发现年度公告',candidate:'已找到候选',ambiguous:'有多份候选',unavailable:'取证失败',
};
const checkStatus:Record<string,string> = {
  waiting_for_both_exchanges:'等待两家交易所原文',
  annual_pair_verified:'两份原文已核验',
  annual_pair_unverified:'原文待复核',
  source_discovery_incomplete:'来源覆盖不完整',
};
const clock = (value:string) => new Intl.DateTimeFormat('zh-CN',{
  timeZone:'Asia/Shanghai',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit',hour12:false,
}).format(new Date(value));

onMounted(async () => {
  try {
    result.value = await getJson<CalendarReport>(endpoint,request.signal);
  } catch (problem) {
    if (!request.signal.aborted) error.value = (problem as Error).message;
  }
});
onBeforeUnmount(()=>request.abort());
</script>

<template>
  <details class="calendar-watch">
    <summary>
      {{result ? result.year+' 年交易日历' : '年度交易日历'}}
      <strong v-if="result"> · {{result.admissionState==='admitted' ? '已准入' : '待准入'}}</strong>
    </summary>
    <p v-if="error" role="status">{{error}}</p>
    <template v-else-if="result">
      <p v-if="result.admission?.admittedAt">正式登记 {{clock(result.admission.admittedAt)}}</p>
      <p v-if="!result.latestScheduled && result.admissionState!=='admitted'">等待首次定时归档</p>
      <p v-for="issue in result.scheduledIssues" :key="issue.attempt">
        {{clock(issue.startedAt)}} · {{issue.state==='pending_archive' ? '取证待归档' : '归档核验失败'}}
      </p>
      <section v-for="(check,i) in [result.latestScheduled,result.latestManual]" :key="i">
        <template v-if="check">
          <p><strong>{{i===0 ? '最近一次定时归档' : '最近一次手工复核'}}</strong>
            · {{clock(check.archiveVerifiedAt || check.checkedAt)}} · {{checkStatus[check.status] ?? check.status}}</p>
          <ul>
            <li v-for="(source,name) in check.sources" :key="name">
              {{exchange[name] ?? name}} · {{sourceStatus[source.status] ?? source.status}}
              · HTTP {{source.httpStatus || '无响应'}} · 收报 {{clock(source.receivedAt)}}
              <a v-for="item in source.candidates" :key="item.url" :href="item.url" target="_blank" rel="noopener">
                {{item.title}} ↗
              </a>
            </li>
          </ul>
        </template>
      </section>
    </template>
    <p v-else role="status">读取公告证据…</p>
    <a :href="result ? apiUrl(endpoint,{year:String(result.year)}) : endpoint" target="_blank" rel="noopener">
      Agent 日历证据 JSON ↗
    </a>
  </details>
</template>

<style scoped>
.calendar-watch{margin:1rem 0;padding:.75rem 1rem;border:1px solid #dce6eb;border-radius:.5rem}
.calendar-watch summary{cursor:pointer}
.calendar-watch p{margin:.55rem 0}
.calendar-watch ul{margin:.3rem 0 .8rem;padding-inline-start:1.3rem}
.calendar-watch li a{display:block;overflow-wrap:anywhere}
</style>
