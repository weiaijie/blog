<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { getJson } from '../state';
import { apiUrl } from '../domain';
import ObservationCoverage from './ObservationCoverage.vue';

interface Source {
  url: string;
  publisher?: string;
  role?: string;
  published_at: string | null;
  captured_at: string;
  evidence_locator?: string;
}
interface PolicyEvent {
  event_id: string;
  event_time: string;
  issuing_body?: string;
  stage: string;
  sources: Source[];
  observed_policy_directions?: string[];
  text_increment?: string | null;
  received_at: string | null;
  feature_ready_at: string | null;
  effective_at: string | null;
  signal_eligible: boolean;
}
interface MarketRow {
  date: string;
  financingBalanceCny: string | null;
  financingBuyCny: string | null;
  financingRepaymentCny: string | null;
  financingNetCny: string | null;
  balanceIdentity?: {status: string; residualCny: string | null};
  stockFinancingBuyCny: string | null;
  turnoverCny: string | null;
  financingBuyShare: string | null;
  relativeTurnover20: string | null;
  breadth: string | null;
}
interface FlowRow {
  symbol: string;
  valuationDate: string;
  totalShares: string | null;
  unitNav: string | null;
  estimatedNetSubscriptionCny: string | null;
  relativeIntensity: string | null;
  featureReadyAt: string | null;
  reason?: string;
}
interface Report {
  version: string;
  policy: {events: PolicyEvent[]};
  etf: {rows: FlowRow[]; limitations?: string; formula?: string};
  market: {rows: MarketRow[]; featureReadyAt?: string; through: string; limitations?: string[]};
}
interface AsOf {
  decisionAt: string;
  events: {event_id: string}[];
}

const endpoint = '/api/v1/research/policy-pilot';
const content = ref<Report>();
const focus = ref('');
const active = computed(() => content.value?.policy.events.find(event => event.event_id === focus.value));
const cutoff = ref('2026-11-27T12:25');
const asOf = ref<AsOf>();
const asOfLink = ref('');
const loading = ref(true);
const querying = ref(false);
const loadError = ref('');
const queryError = ref('');
const lifecycle = new AbortController();
const stages: Record<string, string> = {deployment:'会议部署', details:'方案细则',
  implementation:'正式实施', progress:'进展披露', adjustment:'调整'};

async function load() {
  loading.value = true;
  loadError.value = '';
  try {
    const result = await getJson<Report>(endpoint, lifecycle.signal);
    content.value = result;
    focus.value = result.policy.events.at(-1)?.event_id ?? '';
  } catch (error) {
    if (!lifecycle.signal.aborted) loadError.value = (error as Error).message;
  } finally {
    loading.value = false;
  }
}

async function inspectTime() {
  if (!cutoff.value) return;
  const request = apiUrl(endpoint + '/as-of', {decision_at: cutoff.value + '+08:00'});
  querying.value = true;
  queryError.value = '';
  asOf.value = undefined;
  asOfLink.value = '';
  try {
    asOf.value = await getJson<AsOf>(request, lifecycle.signal);
    asOfLink.value = request;
  } catch (error) {
    if (!lifecycle.signal.aborted) queryError.value = (error as Error).message;
  } finally {
    querying.value = false;
  }
}
const balanceNote = (identity: MarketRow['balanceIdentity']) => identity?.status === 'matched' ? '对账相符'
  : identity?.status === 'mismatch' ? '差额 ' + number(identity.residualCny) + ' 元' : '缺前一日';
const unknown = (value: string | null | undefined) => value ?? '未知';
const beijingTime = (value: string | null | undefined) => value == null ? '未知' : new Date(value)
  .toLocaleString('zh-CN', { timeZone:'Asia/Shanghai', hour12:false });
const number = (value: string | null | undefined, fractional = false) => value == null
  ? '未知' : Number(value).toLocaleString('zh-CN', { maximumFractionDigits: fractional ? 6 : 2 });
const percentage = (value: string | null | undefined) => value == null
  ? '未知' : (100 * Number(value)).toFixed(2) + '%';

onMounted(load);
onBeforeUnmount(() => lifecycle.abort());
</script>

<template>
  <div class="page-title">
    <div>
      <h1>政策与市场研究</h1>
      <p>按原文核对事件和公开时间，查看已取证的 ETF 份额、融资与成交数据。</p>
    </div>
    <a :href="endpoint" class="primary-link" target="_blank" rel="noopener">Agent 数据 JSON ↗</a>
  </div>
  <ObservationCoverage />
  <el-alert v-if="loadError" type="error" :title="loadError" :closable="false"/>
  <el-button v-if="loadError" @click="load">重新加载</el-button>
  <p v-if="loading" role="status" class="muted">正在读取研究证据…</p>
  <template v-if="content">
    <section class="panel">
      <h2>政策事件和来源</h2>
      <div class="policy-grid" v-if="active">
        <div class="event-list" aria-label="已核对事件">
          <button v-for="event in content.policy.events" :key="event.event_id"
            :aria-pressed="event.event_id === focus" @click="focus = event.event_id">
            <strong>{{event.event_time}}</strong>
            <span>{{event.issuing_body ?? '政策事件'}}</span>
          </button>
        </div>
        <div class="event-detail" aria-live="polite">
          <h3>{{active.event_time}} · {{stages[active.stage] ?? active.stage}}</h3>
          <ul v-if="active.observed_policy_directions?.length">
            <li v-for="line in active.observed_policy_directions" :key="line">{{line}}</li>
          </ul>
          <p v-if="active.text_increment">{{active.text_increment}}</p>
          <dl class="event-times">
            <div><dt>系统收报</dt><dd>{{unknown(active.received_at)}}</dd></div>
            <div><dt>处理完成</dt><dd>{{unknown(active.feature_ready_at)}}</dd></div>
            <div><dt>实施时间</dt><dd>{{unknown(active.effective_at)}}</dd></div>
          </dl>
          <ul class="source-list">
            <li v-for="source in active.sources" :key="source.url">
              <a :href="source.url" target="_blank" rel="noopener">{{source.publisher ?? '查看原文'}} ↗</a>
              <span>发布 {{unknown(source.published_at)}}</span>
              <span>本次取回 {{beijingTime(source.captured_at)}}</span>
            </li>
          </ul>
        </div>
      </div>
      <p v-else class="empty">暂无可展示的事件。</p>
      <form class="time-form" @submit.prevent="inspectTime">
        <label>决策时间（北京时间）
          <input v-model="cutoff" type="datetime-local" required :disabled="querying">
        </label>
        <el-button type="primary" native-type="submit" :loading="querying">核对当时可用的事件</el-button>
      </form>
      <el-alert v-if="queryError" type="error" :title="queryError" :closable="false"/>
      <p v-if="asOf" role="status">
        {{asOf.decisionAt}} 可用事件 {{asOf.events.length}} 条。
        <span v-if="!asOf.events.length">事件必须在此时点前收到并处理完成。</span>
        <a :href="asOfLink" target="_blank" rel="noopener">Agent 时点结果 ↗</a>
      </p>
    </section>
    <section class="panel">
      <h2>ETF 份额与单位净值</h2>
      <div v-if="content.etf.rows.length" class="table-scroll" tabindex="0" aria-label="ETF 份额与净值明细">
        <table>
          <thead><tr><th>日期 / ETF</th><th>份额（份）</th><th>单位净值（元）</th>
            <th>估算净申购（元）</th><th>申购强度</th><th>数据状态</th></tr></thead>
          <tbody><tr v-for="row in content.etf.rows" :key="row.valuationDate + row.symbol">
            <th>{{row.valuationDate}} · {{row.symbol}}</th><td>{{number(row.totalShares)}}</td><td>{{number(row.unitNav,true)}}</td>
            <td>{{number(row.estimatedNetSubscriptionCny)}}</td><td>{{percentage(row.relativeIntensity)}}</td>
            <td class="reason">{{row.reason ?? '已核验'}}<br><small>就绪（北京时间） {{beijingTime(row.featureReadyAt)}}</small></td>
          </tr></tbody>
        </table>
      </div>
      <p v-else class="empty">暂无可用的份额与净值组合。</p>
      <p v-if="content.etf.formula" class="muted">{{content.etf.formula}}</p>
      <p v-if="content.etf.limitations" class="muted">{{content.etf.limitations}}</p>
    </section>
    <section class="panel">
      <h2>沪市融资与市场成交</h2>
      <p v-if="content.market.featureReadyAt" class="muted">样本截至 {{content.market.through}}，取证就绪（北京时间） {{beijingTime(content.market.featureReadyAt)}}</p>
      <div v-if="content.market.rows.length" class="table-scroll" tabindex="0" aria-label="融资和成交明细">
        <table>
          <thead><tr><th>交易日</th><th>融资余额（元）</th><th>融资买入（元）</th><th>融资偿还（元）</th><th>融资买入减偿还（元）</th><th>余额对账</th>
            <th>股票融资买入（元）</th><th>同范围股票成交额（元）</th><th>融资买入占比</th><th>相对成交额（倍）</th><th>上涨占比</th></tr></thead>
          <tbody><tr v-for="row in content.market.rows.slice(-8).reverse()" :key="row.date">
            <th>{{row.date}}</th><td>{{number(row.financingBalanceCny)}}</td><td>{{number(row.financingBuyCny)}}</td>
            <td>{{number(row.financingRepaymentCny)}}</td><td>{{number(row.financingNetCny)}}</td>
            <td :class="{mismatch: row.balanceIdentity?.status === 'mismatch'}">{{balanceNote(row.balanceIdentity)}}</td><td>{{number(row.stockFinancingBuyCny)}}</td><td>{{number(row.turnoverCny)}}</td>
            <td>{{percentage(row.financingBuyShare)}}</td><td>{{number(row.relativeTurnover20,true)}}</td><td>{{percentage(row.breadth)}}</td>
          </tr></tbody>
        </table>
      </div>
      <p v-else class="empty">暂无通过核验的行情和融资明细。</p>
      <p v-if="content.market.rows.length > 8" class="muted">显示最近 8 个样本日。完整序列见 Agent 数据。</p>
      <p class="muted">买入占比按沪市主板 A 股与科创板统计。融资余额、买入和偿还前三列为沪市汇总。</p>
      <ul v-if="content.market.limitations?.length" class="muted">
        <li v-for="note in content.market.limitations" :key="note">{{note}}</li>
      </ul>
    </section>
  </template>
</template>

<style scoped>
.policy-grid{display:grid;grid-template-columns:minmax(160px,1fr) minmax(0,3fr);gap:22px}
.event-list{display:grid;align-content:start;gap:8px}
.event-list button{display:grid;gap:5px;text-align:left;background:#f6f9fa;color:#284c5d;border:1px solid #d8e2e8;border-left:3px solid #d8e2e8;padding:12px;border-radius:5px}
.event-list button[aria-pressed=true]{background:#e8f2f3;border-left-color:#397d76}
.event-detail{min-width:0}.event-detail h3{margin-top:0}.event-detail li{line-height:1.8}
.event-times{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;padding:12px 0}
.event-times dt,.source-list span{font-size:12px;color:#517383}
.event-times dd{margin:4px 0 0;overflow-wrap:anywhere}
.source-list{list-style:none;padding:0;margin:0}.source-list li{display:flex;align-items:baseline;flex-wrap:wrap;gap:5px 14px}
.time-form{display:flex;align-items:end;flex-wrap:wrap;gap:12px;margin-top:22px;padding-top:16px;border-top:1px solid #d8e2e8}
.mismatch{color:#a33636}
.reason{text-align:left;white-space:normal;min-width:140px}
@media(max-width:650px){.policy-grid{grid-template-columns:1fr;gap:16px}.event-list{grid-template-columns:1fr 1fr}}
</style>
