<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { apiUrl } from '../domain';
import { getJson } from '../state';

type Issues = Record<string,string>;
type Source = {status:string; readyAt?:string|null; featureReadyAt?:string|null; issues?:Issues};
type Sources = {
  policy: Source & {candidateCount:number|null; reviewedCount:number|null};
  etf: Record<'510300'|'511010',Source>;
  market: {turnover:Source & {cny:string|null}; margin:Source & {balanceIdentity:{status:string; residualCny:string|null}|null}};
};
type Attempt = {
  id:string; phase:string; scheduled:boolean; startedAt:string; archivedAt:string;
  archiveSha256:string; qualified:boolean; sources:Sources|null; failedSources:string[];
};
type Day = {
  day:string; expected:boolean; status:string; archivedAttempts:number; latest:Attempt|null;
  issues:{id:string; status:string}[];
};
type Overview = {
  reportedAt:string; calendarUnknownYear:number|null; nextBefore:string|null;
  counts:{expected:number; archived:number; qualified:number; missing:number};
  firstQualifiedArchive:{session:string; date:string; midtermOn:string; finalOn:string}|null;
  sessions:Day[];
};
const endpoint = '/api/v1/research/observation';
const overview = ref<Overview>();
const selected = ref('');
const detail = ref<Day & {attempts:Attempt[]}>();
const loading = ref(false);
const detailLoading = ref(false);
const error = ref('');
const detailError = ref('');
const lifecycle = new AbortController();
let detailRequest:AbortController|undefined;
const phases:Record<string,string> = {
  qualified:'合格归档', complete:'完整归档', partial:'部分可用', failed:'采集失败',
  interrupted:'采集中断', missing:'未见采集', unverified:'归档待核验',
  pending_archive:'等待归档', not_scheduled:'非计划日', calendar_unknown:'日历待核验',
};
const sourceStates:Record<string,string> = {
  archived:'已归档', verified:'已核验', verified_estimate:'可估算',
  coverage_incomplete:'覆盖不完整', unknown:'待补证', unknown_at_cutoff:'当时不可用',
};
const time = (value?:string|null) => value ? new Date(value).toLocaleString('zh-CN',{
  timeZone:'Asia/Shanghai',hour12:false,
}) : '未就绪';
const label = (value?:Source) => value ? sourceStates[value.status] ?? value.status : '—';
const reason = (key:string) => {
  if (key.startsWith('shares_')) return '清算份额';
  if (key.startsWith('nav_')) return '单位净值';
  if (key.startsWith('catalog_')) return '折算或币种口径';
  return ({margin:'相邻交易日两融汇总未齐',gov_list:'中国政府网索引',csrc_home:'证监会索引'} as Record<string,string>)[key];
};
const missing = (source?:Source) => [...new Set(Object.entries(source?.issues ?? {})
  .map(([key,message])=>reason(key) ?? message))].join('、');
const turnover = (value:string|null) => value===null ? '' : (Number(value)/1e8).toLocaleString('zh-CN',{
  maximumFractionDigits:2,
})+' 亿元';

async function load(before?:string) {
  loading.value = true;
  error.value = '';
  try {
    const result = await getJson<Overview>(apiUrl(endpoint,before ? {before} : {}),lifecycle.signal);
    overview.value = before && overview.value
      ? {...result,sessions:[...overview.value.sessions,...result.sessions]} : result;
    if (!before && selected.value) void openDay(selected.value);
  } catch (problem) {
    if (!lifecycle.signal.aborted) error.value = (problem as Error).message;
  } finally {
    loading.value = false;
  }
}
async function openDay(day:string) {
  detailRequest?.abort();
  const request = new AbortController();
  detailRequest = request;
  selected.value = day;
  detail.value = undefined;
  detailLoading.value = true;
  detailError.value = '';
  try {
    const result = await getJson<{session:Day & {attempts:Attempt[]}}>(
      apiUrl(endpoint,{day}),request.signal,
    );
    if (detailRequest===request) detail.value = result.session;
  } catch (problem) {
    if (!request.signal.aborted) detailError.value = (problem as Error).message;
  } finally {
    if (detailRequest===request) detailLoading.value = false;
  }
}

onMounted(()=>load());
onBeforeUnmount(()=>{lifecycle.abort();detailRequest?.abort();});
</script>

<template>
  <section class="panel" aria-labelledby="coverage-title">
    <div class="section-head coverage-head">
      <div>
        <h2 id="coverage-title">前瞻数据覆盖</h2>
        <p class="muted" v-if="overview">北京时间 {{time(overview.reportedAt)}} 核对</p>
      </div>
      <div class="coverage-actions">
        <el-button :loading="loading" @click="load()">刷新覆盖</el-button>
        <a :href="endpoint" target="_blank" rel="noopener">Agent 覆盖 JSON ↗</a>
      </div>
    </div>
    <p v-if="loading && !overview" role="status">正在核对日级归档…</p>
    <el-alert v-if="error" :title="error" type="error" :closable="false"/>
    <div v-if="overview">
      <p v-if="overview.firstQualifiedArchive" class="milestone">
        观察期自 <strong>{{overview.firstQualifiedArchive.date}}</strong> 起算，
        6 个月复盘 {{overview.firstQualifiedArchive.midtermOn}}，
        12 个月结题 {{overview.firstQualifiedArchive.finalOn}}。
      </p>
      <p v-else class="milestone"><strong>观察期尚未起算</strong> · 等待首个完整的定时归档通过核验。</p>
      <dl class="coverage-counts">
        <div><dt>应采交易日</dt><dd>{{overview.counts.expected}}</dd></div>
        <div><dt>已有归档</dt><dd>{{overview.counts.archived}}</dd></div>
        <div><dt>合格归档</dt><dd>{{overview.counts.qualified}}</dd></div>
        <div><dt>未见采集</dt><dd>{{overview.counts.missing}}</dd></div>
      </dl>
      <el-alert v-if="overview.calendarUnknownYear" type="warning" :closable="false"
        :title="overview.calendarUnknownYear+' 年交易日历待核验'"/>
      <div v-if="overview.sessions.length" class="table-scroll" tabindex="0" aria-label="按交易日核对采集来源">
        <table class="coverage-table">
          <thead><tr><th scope="col">交易日</th><th scope="col">归档状态</th>
            <th scope="col">政策</th><th scope="col">510300</th><th scope="col">511010</th>
            <th scope="col">沪市成交</th><th scope="col">沪市两融</th><th scope="col">归档次数</th></tr></thead>
          <tbody>
            <tr v-for="row in overview.sessions" :key="row.day" :class="{focused: row.day===selected}">
              <th scope="row"><button class="text-button date-button" :aria-pressed="row.day===selected"
                @click="openDay(row.day)">{{row.day}}</button></th>
              <td><strong>{{phases[row.status] ?? row.status}}</strong><small v-if="!row.expected">计划外</small></td>
              <td>{{label(row.latest?.sources?.policy)}}</td>
              <td>{{label(row.latest?.sources?.etf['510300'])}}</td>
              <td>{{label(row.latest?.sources?.etf['511010'])}}</td>
              <td>{{label(row.latest?.sources?.market.turnover)}}</td>
              <td>{{label(row.latest?.sources?.market.margin)}}</td>
              <td>{{row.archivedAttempts}}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else>当前没有可列出的交易日。</p>
      <el-button v-if="overview.nextBefore" class="older" :loading="loading"
        @click="load(overview.nextBefore ?? undefined)">更早的交易日</el-button>
      <p v-if="detailLoading" role="status">正在核对 {{selected}} 的采集记录…</p>
      <el-alert v-if="detailError" :title="detailError" type="error" :closable="false"/>
      <div v-if="detail" class="coverage-detail" aria-live="polite">
        <div class="section-head coverage-head">
          <h3>{{detail.day}} · 采集与补采记录</h3>
          <a :href="apiUrl(endpoint,{day:detail.day})" target="_blank" rel="noopener">Agent 当日 JSON ↗</a>
        </div>
        <p v-for="issue in detail.issues" :key="issue.id">{{phases[issue.status] ?? issue.status}} · {{issue.id}}</p>
        <p v-if="!detail.attempts.length">这一天没有通过哈希核验的归档。</p>
        <ol v-else class="attempts">
          <li v-for="attempt in detail.attempts" :key="attempt.id">
            <p class="attempt-title"><strong>{{phases[attempt.phase] ?? attempt.phase}}</strong>
              <span>{{attempt.scheduled ? '定时采集' : '手工复查'}}</span>
              <span v-if="attempt.qualified">计入合格归档</span>
            </p>
            <p class="muted">开始 {{time(attempt.startedAt)}} · 归档 {{time(attempt.archivedAt)}}</p>
            <dl v-if="attempt.sources" class="attempt-sources">
              <div><dt>政策原文</dt><dd>{{label(attempt.sources.policy)}} · 候选 {{attempt.sources.policy.candidateCount ?? '未知'}} 条</dd></div>
              <div v-for="(fund,symbol) in attempt.sources.etf" :key="symbol"><dt>{{symbol}} 份额净值</dt>
                <dd>{{label(fund)}} · {{fund.featureReadyAt ? time(fund.featureReadyAt) : missing(fund) || '等待来源'}}</dd></div>
              <div><dt>沪市成交</dt><dd>{{label(attempt.sources.market.turnover)}}
                {{turnover(attempt.sources.market.turnover.cny)}} <small v-if="attempt.sources.market.turnover.readyAt">
                {{time(attempt.sources.market.turnover.readyAt)}}</small></dd></div>
              <div><dt>沪市两融</dt><dd>{{label(attempt.sources.market.margin)}}
                {{missing(attempt.sources.market.margin)}}
                <small v-if="attempt.sources.market.margin.readyAt">{{time(attempt.sources.market.margin.readyAt)}}</small>
                <small v-if="attempt.sources.market.margin.balanceIdentity?.status==='mismatch'">
                  余额对账差额 {{attempt.sources.market.margin.balanceIdentity.residualCny}} 元
                </small></dd></div>
            </dl>
            <p v-else-if="attempt.failedSources.length">失败环节 {{attempt.failedSources.join('、')}}</p>
            <details class="receipt"><summary>归档校验值</summary><code>{{attempt.archiveSha256}}</code></details>
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>

<style scoped>
.coverage-head{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px 16px}
.coverage-head h2,.coverage-head h3{margin:0}
.coverage-head p{margin:6px 0 0}
.coverage-actions{display:flex;align-items:center;flex-wrap:wrap;gap:12px}
.milestone{padding:12px 14px;background:#edf5f4;border-left:3px solid #35776c;margin:14px 0}
.coverage-counts{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}
.coverage-counts dt,.attempt-sources dt{color:#526b7b;font-size:12px}
.coverage-counts dd{font-size:22px;font-weight:650;margin:4px 0;font-variant-numeric:tabular-nums}
.focused{background:#edf5f4}.coverage-table td small{display:block;color:#526b7b}.date-button{min-height:38px}
.older{margin-top:12px}.coverage-detail{border-top:1px solid #d8e2e8;margin-top:18px;padding-top:16px}
.attempts{list-style:none;padding:0}.attempts li{border:1px solid #d8e2e8;border-radius:5px;margin:10px 0;padding:12px}
.attempt-title{display:flex;flex-wrap:wrap;gap:6px 14px}.attempt-title,.attempts p{margin:0 0 8px}
.attempt-sources{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px 16px;margin:12px 0}
.attempt-sources dd{margin:3px 0;line-height:1.65}.attempt-sources small{display:block}
.receipt{color:#526b7b}.receipt code{display:block;overflow-wrap:anywhere;margin-top:8px}
@media(max-width:650px){.coverage-counts{grid-template-columns:repeat(2,1fr)}}
</style>
