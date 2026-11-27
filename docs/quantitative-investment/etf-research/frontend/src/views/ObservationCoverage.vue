<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { apiUrl } from '../domain';
import { getJson } from '../state';
import ObservationMonthly from './ObservationMonthly.vue';

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
type DecisionClock = {scheduledAt:string|null; deadline:string|null};
type DecisionAttempt = {
  id:string; status:string; startedAt?:string; archivedAt?:string; archiveSha256?:string;
  availableVariants?:Record<string,boolean>; featureGaps?:Record<string,string|null>; forecastProduced?:boolean;
};
type Decision = DecisionClock & {status:string; latest?:DecisionAttempt|null; attempts?:DecisionAttempt[]};
type LabelMetrics = {terminalReturn:string; maxDrawdown:string};
type LabelAttempt = {
  id:string; status:string; archivedAt?:string; readyAt?:string|null; archiveSha256?:string;
  gaps?:Record<string,string|{reason:string}>; results?:Record<string,Record<string,LabelMetrics>>|null;
};
type OutcomeLabel = {status:string; sessions:string[]; notBefore:string|null; readyAt:string|null; attempts?:LabelAttempt[]};
type FitProgress = {status:string; trainingDays:number};
type ModelProgress = {status:string; firstFoldStart?:string; fold:{start:string;end:string}|null;
  comparisons?:Record<string,FitProgress>; modelReceipt?:{modelSealedAt:string;archiveSha256:string}};
type Prediction = {status:string; trainingDays?:number; eventIds?:string[]; baseline?:number[]; expanded?:number[]};
type ForecastAttempt = {id:string; status:string; sealedAt?:string; reason?:string|null; archiveSha256?:string;
  comparisons?:Record<string,Prediction>; modelArchiveSha256?:string|null};
type Forecast = {status:string; deadline:string|null; readyAt:string|null; attempts?:ForecastAttempt[]};
type Day = {
  day:string; expected:boolean; status:string; archivedAttempts:number; latest:Attempt|null;
  issues:{id:string; status:string}[]; decision:Decision; label:OutcomeLabel; forecast:Forecast; modelProgress?:ModelProgress;
};
type EvidenceGate = {pairs:number; folds:number;policyEvents:number};
type AssessmentGroup = {status:string; completedPairs:number|null; folds:number|null; policyEvents:number|null;
  shortfall:EvidenceGate|null; selectedWindows:number|null;matchedWindows:number|null};
type EvaluationProgress = {
  status:string; archiveState:string; assessedAt:string|null; verifiedAt:string|null; archiveSha256:string|null;
  archiveIssues:{unverified:number;pending:number}; originSinceArchive:boolean;
  thresholds:EvidenceGate; comparisons:Record<string,AssessmentGroup>;
};
type Overview = {
  reportedAt:string; calendarUnknownYear:number|null; nextBefore:string|null;
  counts:{expected:number; archived:number; qualified:number; missing:number};
  firstQualifiedArchive:{session:string; date:string; midtermOn:string; finalOn:string}|null;
  sessions:Day[]; nextDecision:DecisionClock|null;
  decisionCounts:{expected:number; sealedOnTime:number; eligibleInputDays:number; gaps:number};
  labelCounts:{due:number; ready:number; gaps:number; holding:number; unknownCalendar:number};
  modelProgress:ModelProgress;
  evaluation:EvaluationProgress;
  forecastCounts:{due:number; sealedDays:number; gaps:number; sealedPairs:Record<string,number>;unknownCalendar:number};
};
const endpoint = '/api/v1/research/observation';
const evaluationEndpoint = endpoint+'/evaluation';
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
  awaiting_market_close:'等待收盘',
};
const decisionStates:Record<string,string> = {
  prelaunch:'封存启动前', not_scheduled:'休市', calendar_unknown:'日历待核验',
  pending:'待封存', pending_archive:'封存进行中', missing:'未见封存', incomplete:'封存未完成',
  unverified:'封存校验失败', missed_deadline:'超过截止', failed:'封存失败',
  missing_inputs:'基线缺输入', study_origin_pending:'已按时封存，待观察起点',
  eligible_inputs:'已按时封存，可入样候选',
};
const labelStates:Record<string,string> = {
  decision_ineligible:'暂无合格决策', calendar_unverified:'持有日历待核验',
  holding_period_incomplete:'持有期未满', mature_unsealed:'到期，待封存',
  pending_archive:'等待归档', unverified:'标签校验失败',
  evidence_missing:'证据缺失', evidence_complete:'标签已就绪',
};
const labelGaps:Record<string,string> = {
  opening_evidence_missing:'缺少开盘证据', opening_sources_conflict:'开盘证据冲突',
  opening_quote_differs_from_admitted_ohlc:'开盘快照与三源行情冲突',
  ex_dividend_timing_unverified:'除息时点待核验', opening_reference_change_unexplained:'开盘参考价变化待核验',
  price_evidence_invalid:'行情证据校验失败', price_evidence_not_ready:'行情证据未就绪',
  anchor_price_version_differs_from_sealed_decision:'前收盘版本与封存决策不一致',
  published_price_revision_or_missing_day:'已发布行情缺日或发生修订',
  published_dividend_version_conflict:'分红证据版本冲突',
};
const modelStates:Record<string,string> = {
  observation_origin_pending:'等待首个合格归档', training_accumulation:'积累训练样本',
  awaiting_model:'等待该折模型封存', model_verified:'该折模型已就绪',
  model_unverified:'模型归档校验失败', insufficient_training:'训练样本不足',
  observation_ended:'已至观察期末', fitted:'已拟合',
};
const forecastStates:Record<string,string> = {
  ...modelStates, not_scheduled:'无预测安排', calendar_unverified:'预测日历待核验',
  holding_window_crosses_fold:'持有期跨折', pending:'等待截止', pending_archive:'等待归档',
  incomplete:'归档未完成', missing:'未见封存', unverified:'预测核验失败',
  no_prediction:'未产出预测', sealed_predictions:'预测已按时封存', missed_deadline:'归档超过截止',
  outside_scheduled_cutoff:'错过计划时点', model_not_ready:'当时模型未就绪',
  evidence_unavailable:'证据待核验', decision_missing:'缺当日决策',
  decision_missing_inputs:'决策输入不齐', decision_study_origin_pending:'当时观察期尚未起算',
  inputs_missing:'扩展输入不齐', policy_event_previously_seen:'政策事件已在训练或先前折使用',
  predicted:'已计算预测',
};
const evaluationStates:Record<string,string> = {
  observation_origin_pending:'等待首个合格归档', awaiting_evaluation:'等待评估任务封存',
  observation_in_progress:'观察期间，累计覆盖证据', evaluation_available:'已至评估阶段',
  final_labels_pending:'等待最后一段标签', calendar_unverified:'交易日历待核验',
  insufficient_samples:'样本不足', improved:'达到主要检验的改善标准', not_established:'尚未达到改善标准',
  uncertain:'区间无法确定', exploratory:'探索性结果',
};
const metricProgress = (value:number|null, goal:number) => value===null ? '待核验' : value+' / '+goal;
const labelGap = (code:string|{reason:string}) => {
  const key=typeof code==='string' ? code : code.reason;
  return labelGaps[key] ?? key;
};
const percent = (value:string|number) => Number(value).toLocaleString('zh-CN',{style:'percent',maximumFractionDigits:3});
const variants:Record<string,string> = {
  baseline:'量价基线', policy:'加入政策', etf:'加入 ETF 份额净值', margin:'加入两融', combined:'全量增量',
};
const featureNames:Record<string,string> = {
  stockReturn5:'股票 ETF 五日收益', stockReturn20:'股票 ETF 二十日收益', stockVol20:'股票 ETF 波动',
  bondReturn5:'国债 ETF 五日收益', bondReturn20:'国债 ETF 二十日收益', bondVol20:'国债 ETF 波动',
  turnover20:'沪市成交强度', policyActiveCount:'政策事件数', stockShareFlow:'510300 份额净值',
  bondShareFlow:'511010 份额净值', stockFinancingBuyShare:'沪市融资买入占比',
};
const gapReasons:Record<string,string> = {
  archive_missing:'未找到来源归档', archive_not_ready:'来源归档晚于读取时点',
  archive_proof_invalid:'来源归档校验失败', attempt_not_verified:'采集核验未完成',
  price_publication_or_matching_closes_not_ready:'同日行情或复权证据待核验',
  price_publication_proof_invalid:'行情凭证校验失败', required_turnover_not_ready:'成交额窗口缺日',
  warmup_proof_invalid:'成交额历史凭证校验失败', same_valuation_day_basis_missing:'同估值日证据未齐',
  matched_margin_basis_missing:'同口径两融证据未齐', five_decision_intervals_without_certified_review:'五个政策区间覆盖未齐',
  policy_review_proof_invalid:'政策审核凭证校验失败',
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
      <section class="decision-summary" aria-labelledby="decision-title">
        <div class="section-head coverage-head">
          <div>
            <h3 id="decision-title">08:55 决策封存</h3>
            <p v-if="overview.nextDecision" class="muted">下次启动 {{time(overview.nextDecision.scheduledAt)}}（北京时间）</p>
            <p v-else class="muted">下一次启动等待交易日历核验。</p>
          </div>
        </div>
        <dl class="coverage-counts">
          <div><dt>已到截止</dt><dd>{{overview.decisionCounts.expected}}</dd></div>
          <div><dt>按时封存</dt><dd>{{overview.decisionCounts.sealedOnTime}}</dd></div>
          <div><dt>可入样候选</dt><dd>{{overview.decisionCounts.eligibleInputDays}}</dd></div>
          <div><dt>封存缺口</dt><dd>{{overview.decisionCounts.gaps}}</dd></div>
        </dl>
        <p class="muted">可入样候选需等待五交易日收益与回撤标签核验。</p>
      </section>
      <section class="decision-summary" aria-labelledby="label-title">
        <h3 id="label-title">五交易日标签</h3>
        <dl class="coverage-counts">
          <div><dt>持有期未满</dt><dd>{{overview.labelCounts.holding}}</dd></div>
          <div><dt>到期窗口</dt><dd>{{overview.labelCounts.due}}</dd></div>
          <div><dt>标签已就绪</dt><dd>{{overview.labelCounts.ready}}</dd></div>
          <div><dt>到期缺口</dt><dd>{{overview.labelCounts.gaps}}</dd></div>
        </dl>
        <p v-if="overview.labelCounts.unknownCalendar" class="muted">另有 {{overview.labelCounts.unknownCalendar}} 个候选窗口待核验交易日历。</p>
      </section>
      <section class="decision-summary" aria-labelledby="forecast-title">
        <h3 id="forecast-title">训练与预测</h3>
        <p>{{modelStates[overview.modelProgress.status] ?? overview.modelProgress.status}}
          <span v-if="overview.modelProgress.firstFoldStart"> · 首折 {{overview.modelProgress.firstFoldStart}}</span>
          <span v-if="overview.modelProgress.fold"> · {{overview.modelProgress.fold.start}} 至 {{overview.modelProgress.fold.end}} 前</span>
          <span v-if="overview.modelProgress.modelReceipt"> · 模型封存 {{time(overview.modelProgress.modelReceipt.modelSealedAt)}}</span>
        </p>
        <dl class="coverage-counts">
          <div><dt>应预测日</dt><dd>{{overview.forecastCounts.due}}</dd></div>
          <div><dt>按时封存日</dt><dd>{{overview.forecastCounts.sealedDays}}</dd></div>
          <div><dt>预测缺口</dt><dd>{{overview.forecastCounts.gaps}}</dd></div>
        </dl>
        <dl v-if="overview.modelProgress.comparisons || overview.forecastCounts.sealedDays" class="attempt-sources">
          <div v-for="(pairs,name) in overview.forecastCounts.sealedPairs" :key="name">
            <dt>{{variants[name] ?? name}}</dt>
            <dd v-if="overview.modelProgress.comparisons?.[name]">
              {{modelStates[overview.modelProgress.comparisons[name].status] ?? overview.modelProgress.comparisons[name].status}}
              · 训练 {{overview.modelProgress.comparisons[name].trainingDays}} 行
            </dd>
            <dd>已封存 {{pairs}} 对</dd>
          </div>
        </dl>
        <p v-if="overview.forecastCounts.unknownCalendar" class="muted">
          {{overview.forecastCounts.unknownCalendar}} 个预测日期仍待核验交易日历。
        </p>
      </section>
      <section class="decision-summary" aria-labelledby="evaluation-title">
        <div class="section-head coverage-head">
          <div>
            <h3 id="evaluation-title">样本外评估</h3>
            <p>{{evaluationStates[overview.evaluation.status] ?? overview.evaluation.status}}</p>
          </div>
          <a :href="apiUrl(evaluationEndpoint,overview.evaluation.archiveSha256 ? {archive:overview.evaluation.archiveSha256} : {})"
            target="_blank" rel="noopener">查看评估 JSON ↗</a>
        </div>
        <p class="muted" v-if="overview.evaluation.assessedAt">
          评估时点 {{time(overview.evaluation.assessedAt)}} · 归档核验 {{time(overview.evaluation.verifiedAt)}}
        </p>
        <p class="muted" v-else>{{overview.evaluation.archiveState==='unverified' ? '评估归档校验未通过' : '等待首份定时评估归档'}}</p>
        <p v-if="overview.evaluation.originSinceArchive" class="muted">观察期已起算，表内保留上一次归档时的结果。</p>
        <p v-if="overview.evaluation.archiveIssues.unverified || overview.evaluation.archiveIssues.pending" class="muted">
          {{overview.evaluation.archiveIssues.unverified}} 份未通过核验 · {{overview.evaluation.archiveIssues.pending}} 份等待归档。
        </p>
        <div class="table-scroll" tabindex="0" aria-label="各组评估门槛">
          <table class="coverage-table">
            <thead><tr><th scope="col">比较</th><th scope="col">状态</th><th scope="col">已配对日期</th>
              <th scope="col">覆盖折</th><th scope="col">独立政策事件</th><th scope="col">经济对照窗口</th></tr></thead>
            <tbody>
              <tr v-for="(group,name) in overview.evaluation.comparisons" :key="name">
                <th scope="row">{{variants[name] ?? name}}</th>
                <td>{{evaluationStates[group.status] ?? group.status}}</td>
                <td>{{metricProgress(group.completedPairs,overview.evaluation.thresholds.pairs)}}
                  <small v-if="group.shortfall?.pairs">还差 {{group.shortfall.pairs}} 日</small>
                </td>
                <td>{{metricProgress(group.folds,overview.evaluation.thresholds.folds)}}
                  <small v-if="group.shortfall?.folds">还差 {{group.shortfall.folds}} 折</small>
                </td>
                <td>{{name==='policy' || name==='combined' ? metricProgress(group.policyEvents,overview.evaluation.thresholds.policyEvents) : '—'}}
                  <small v-if="group.shortfall?.policyEvents">还差 {{group.shortfall.policyEvents}} 个</small>
                </td>
                <td>{{group.selectedWindows===null ? '待核验' : metricProgress(group.matchedWindows,group.selectedWindows)}}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <ObservationMonthly />
      <el-alert v-if="overview.calendarUnknownYear" type="warning" :closable="false"
        :title="overview.calendarUnknownYear+' 年交易日历待核验'"/>
      <div v-if="overview.sessions.length" class="table-scroll" tabindex="0" aria-label="按交易日核对采集来源">
        <table class="coverage-table">
          <thead><tr><th scope="col">交易日</th><th scope="col">归档状态</th><th scope="col">决策封存</th><th scope="col">五日标签</th><th scope="col">预测</th>
            <th scope="col">政策</th><th scope="col">510300</th><th scope="col">511010</th>
            <th scope="col">沪市成交</th><th scope="col">沪市两融</th><th scope="col">归档次数</th></tr></thead>
          <tbody>
            <tr v-for="row in overview.sessions" :key="row.day" :class="{focused: row.day===selected}">
              <th scope="row"><button class="text-button date-button" :aria-pressed="row.day===selected"
                @click="openDay(row.day)">{{row.day}}</button></th>
              <td><strong>{{phases[row.status] ?? row.status}}</strong></td>
              <td>{{decisionStates[row.decision.status] ?? row.decision.status}}</td>
              <td>{{labelStates[row.label.status] ?? row.label.status}}</td>
              <td>{{forecastStates[row.forecast.status] ?? row.forecast.status}}</td>
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
          <h3>{{detail.day}} · 决策与采集记录</h3>
          <a :href="apiUrl(endpoint,{day:detail.day})" target="_blank" rel="noopener">Agent 当日 JSON ↗</a>
        </div>
        <section class="decision-detail" aria-label="当日决策封存">
          <p><strong>决策封存 · {{decisionStates[detail.decision.status] ?? detail.decision.status}}</strong>
            <span v-if="detail.decision.deadline" class="muted">截止 {{time(detail.decision.deadline)}}</span>
          </p>
          <ol v-if="detail.decision.attempts?.length" class="attempts">
            <li v-for="attempt in detail.decision.attempts" :key="attempt.id">
              <p class="attempt-title"><strong>{{decisionStates[attempt.status] ?? attempt.status}}</strong>
                <span v-if="attempt.archivedAt">归档 {{time(attempt.archivedAt)}}</span></p>
              <dl v-if="attempt.availableVariants" class="attempt-sources">
                <div v-for="(available,name) in attempt.availableVariants" :key="name">
                  <dt>{{variants[name] ?? name}}</dt><dd>{{available ? '输入齐备' : '输入缺失'}}</dd>
                </div>
              </dl>
              <ul v-if="attempt.featureGaps && Object.keys(attempt.featureGaps).length" class="decision-gaps">
                <li v-for="(gap,name) in attempt.featureGaps" :key="name">
                  {{featureNames[name] ?? name}} · {{gap ? gapReasons[gap] ?? gap : '证据待核验'}}
                </li>
              </ul>
              <details v-if="attempt.archiveSha256" class="receipt"><summary>决策归档校验值</summary>
                <code>{{attempt.archiveSha256}}</code></details>
            </li>
          </ol>
        </section>
        <section class="decision-detail" aria-label="当日五交易日标签">
          <p><strong>五交易日标签 · {{labelStates[detail.label.status] ?? detail.label.status}}</strong>
            <span v-if="detail.label.readyAt" class="muted">实际就绪 {{time(detail.label.readyAt)}}</span>
            <span v-else-if="detail.label.notBefore" class="muted">到期 {{time(detail.label.notBefore)}}</span>
          </p>
          <p v-if="detail.label.sessions.length" class="muted">持有日 {{detail.label.sessions.join('、')}}</p>
          <ol v-if="detail.label.attempts?.length" class="attempts">
            <li v-for="attempt in detail.label.attempts" :key="attempt.id">
              <p class="attempt-title"><strong>{{labelStates[attempt.status] ?? attempt.status}}</strong>
                <span v-if="attempt.archivedAt">归档 {{time(attempt.archivedAt)}}</span></p>
              <dl v-if="attempt.results?.stock_bond_50_50?.base" class="attempt-sources" aria-label="股债各半基准费用">
                <div><dt>五日净收益</dt><dd>{{percent(attempt.results.stock_bond_50_50.base.terminalReturn)}}</dd></div>
                <div><dt>最大收盘回撤</dt><dd>{{percent(attempt.results.stock_bond_50_50.base.maxDrawdown)}}</dd></div>
              </dl>
              <ul v-if="attempt.gaps && Object.keys(attempt.gaps).length" class="decision-gaps">
                <li v-for="(gap,name) in attempt.gaps" :key="name">{{name}} · {{labelGap(gap)}}</li>
              </ul>
              <details v-if="attempt.archiveSha256" class="receipt"><summary>标签归档校验值</summary>
                <code>{{attempt.archiveSha256}}</code></details>
            </li>
          </ol>
        </section>
        <section class="decision-detail" aria-label="当日训练与预测">
          <p><strong>预测 · {{forecastStates[detail.forecast.status] ?? detail.forecast.status}}</strong>
            <span v-if="detail.forecast.readyAt" class="muted">实际封存 {{time(detail.forecast.readyAt)}}</span>
            <span v-else-if="detail.forecast.deadline" class="muted">截止 {{time(detail.forecast.deadline)}}</span>
          </p>
          <dl v-if="detail.modelProgress?.comparisons" class="attempt-sources">
            <div v-for="(fit,name) in detail.modelProgress.comparisons" :key="name">
              <dt>{{variants[name] ?? name}}</dt><dd>训练 {{fit.trainingDays}} 行 · {{modelStates[fit.status] ?? fit.status}}</dd>
            </div>
          </dl>
          <ol v-if="detail.forecast.attempts?.length" class="attempts">
            <li v-for="attempt in detail.forecast.attempts" :key="attempt.id">
              <p class="attempt-title"><strong>{{forecastStates[attempt.status] ?? attempt.status}}</strong>
                <span v-if="attempt.reason">{{forecastStates[attempt.reason] ?? attempt.reason}}</span>
                <span v-if="attempt.sealedAt">归档 {{time(attempt.sealedAt)}}</span></p>
              <dl v-if="attempt.comparisons" class="attempt-sources">
                <div v-for="(item,name) in attempt.comparisons" :key="name">
                  <dt>{{variants[name] ?? name}}</dt>
                  <dd>{{forecastStates[item.status] ?? item.status}}</dd>
                  <dd v-if="item.baseline">基线收益 {{percent(item.baseline[0])}} · 回撤 {{percent(item.baseline[1])}}</dd>
                  <dd v-if="item.expanded">扩展收益 {{percent(item.expanded[0])}} · 回撤 {{percent(item.expanded[1])}}</dd>
                </div>
              </dl>
              <details v-if="attempt.archiveSha256" class="receipt"><summary>预测归档校验值</summary>
                <code>{{attempt.archiveSha256}}</code></details>
            </li>
          </ol>
        </section>
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
.decision-summary h3{margin:0}
.decision-summary,.decision-detail{border-top:1px solid #d8e2e8;padding-top:12px;margin:14px 0}
.decision-detail span{margin-inline-start:10px}
.decision-gaps{padding-inline-start:18px;margin:8px 0}
.attempts .decision-gaps li{border:0;padding:0;margin:4px 0}
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
