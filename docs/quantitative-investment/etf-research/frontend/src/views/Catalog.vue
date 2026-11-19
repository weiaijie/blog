<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { agentManifest, money, parsePlan, type Period, type Plan } from '../domain';
import { getJson } from '../state';

interface Entry {
  id: string; label: string; group: string; rule: string; source: string;
  reports: {title: string; url: string}[]; plan: Plan; periods: Record<string, Period>;
}
const catalog = ref<Entry[]>([]);
const query = ref('');
const group = ref('');
const selected = ref('');
const failure = ref('');
const loaded = ref(false);
const groups = computed(() => [...new Set(catalog.value.map(row => row.group))]);
const rows = computed(() => {
  const keyword = query.value.trim().toLowerCase();
  return catalog.value.filter(row => (!group.value || row.group === group.value)
    && [row.label, row.id, row.rule, ...row.reports.map(r => r.title)].join(' ').toLowerCase().includes(keyword));
});
const detail = computed(() => rows.value.find(row => row.id === selected.value) ?? rows.value[0]);
async function load() {
  failure.value = '';
  try {
    const result = await getJson<{entries: Entry[]}>('/strategy-catalog.json');
    catalog.value = result.entries.map(row => ({...row, plan: parsePlan(row.plan)}));
    loaded.value = true;
  } catch (error) {
    failure.value = (error as Error).message;
  }
}
onMounted(load);
</script>

<template>
  <div class="page-title"><div><h1>策略中心</h1><p>查找模型或市场基准，查看规则和历史结果，用同一套参数逐日回放。</p></div>
    <a href="/strategy-catalog.json" target="_blank" rel="noopener">Agent 台账 JSON ↗</a></div>
  <el-alert v-if="failure" :title="failure" type="error" :closable="false"/>
  <el-button v-if="failure" @click="load">重新加载台账</el-button>
  <p v-else-if="!loaded" role="status">正在读取策略台账…</p>
  <template v-if="loaded">
    <section class="panel">
      <div class="actions"><label>搜索模型、因子或报告<input v-model="query" type="search" placeholder="例如 ADX、国债"></label>
        <label>类别<select v-model="group"><option value="">全部类别</option><option v-for="g in groups" :key="g">{{g}}</option></select></label></div>
      <p role="status">{{rows.length}} / {{catalog.length}} 项</p>
      <div class="choices"><button v-for="row in rows" :key="row.id" type="button" :aria-pressed="detail?.id===row.id" @click="selected=row.id">{{row.label}}</button></div>
      <p v-if="!rows.length">没有匹配项。可清空关键词或切换类别。</p>
    </section>
    <section v-if="detail" class="panel">
      <p class="eyebrow">{{detail.group}}</p><h2>{{detail.label}}</h2><p>{{detail.rule}}</p>
      <p>{{detail.plan.start}} 至 {{detail.plan.end}} · 每户 {{money(detail.plan.capital)}} 元 · 基准费用</p>
      <p class="muted">沪深300 / 标普500 / 恒生 / 国债配比 {{detail.plan.portfolios[0]}} · 数据版本 {{detail.plan.dataset}}</p>
      <div class="table-scroll"><table><thead><tr><th>持有期</th><th>到期窗口</th><th>赚钱次数</th><th>年化 ≥ 4%</th><th>最差到期盈亏（元）</th></tr></thead>
        <tbody><tr v-for="(period,year) in detail.periods" :key="year"><th>{{year}} 年</th><td>{{period.count}}</td><td>{{period.profitable}}</td><td>{{period.reached}}</td><td>{{money(period.worstPnl)}}</td></tr></tbody></table></div>
      <p class="muted">相邻窗口共享交易日。统计采用上列归档参数。</p>
      <div class="actions"><RouterLink class="primary-link" :to="{path:'/research',query:{plan:JSON.stringify(detail.plan)}}">用报告参数回放</RouterLink>
        <a :href="agentManifest(detail.plan).requests.replay" target="_blank" rel="noopener">Agent 首日请求 ↗</a></div>
      <h3>研究依据</h3><ul><li v-for="report in detail.reports" :key="report.url"><a :href="report.url" target="_blank" rel="noopener">{{report.title}}</a></li>
        <li><a :href="detail.source" target="_blank" rel="noopener">查看该版本源码 ↗</a></li></ul>
    </section>
  </template>
</template>

<style scoped>
.choices{display:flex;flex-wrap:wrap;gap:8px}.choices button{background:#fff;color:#20475d;border:1px solid #afc3ce;border-radius:4px;padding:9px 14px;cursor:pointer}
.choices button[aria-pressed=true]{background:#173e52;color:white;border-color:#173e52}
li{margin:8px 0}
</style>
