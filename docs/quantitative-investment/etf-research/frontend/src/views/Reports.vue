<script setup lang="ts">
const reports=[
['321个加回费用仍落后窗口','股票亏损、国债收益差与短空档；三个视角分别对账。','adx-shortfall','2026-11-12-adx-shortfall'],
['交易体检与费用','23轮持仓、四档费用；检查成本与频繁换仓。','adx-trades','2026-11-12-adx-trades'],
['ADX与纯国债','同日起点、逐年及非重叠区间，检查收益来自哪里。','adx-bond','2026-11-11-adx-bond'],
['量价、KDJ、ADX','独立确认条件与原三因子比较。','factor-lab','2026-11-11-technical-factors'],
['三批比一次多亏821.26元','2021-10-29至2022-10-31，按交易日拆解。','method-gap-case','2026-11-10-method-gap'],
['多因子514个低收益窗口','与同一起点固定配置对照，检查全债与成本影响。','factor-shortfall','2026-11-10-multifactor-shortfall'],
];
const root='https://github.com/weiaijie/blog/blob/redesign-pc/docs/quantitative-investment/etf-research/';
</script>
<template><div class="page-title"><div><h1>研究报告</h1><p>这里是已归档的固定实验，采用报告自身的日期与参数，不受右上角当前方案控制。</p></div></div><section class="panel report-list"><article v-for="[title,description,anchor,folder] in reports" :key="anchor"><h2>{{title}}</h2><p>{{description}}</p><div class="actions"><a :href="'/backtest.html#'+anchor">打开完整交互报告 ↗</a><a :href="root+'reports/'+folder+'/README.md'" target="_blank" rel="noopener">GitHub证据</a></div></article></section><section class="panel"><h2>计划与接续</h2><p><a :href="root+'CONTINUATION.md'" target="_blank" rel="noopener">当前进度与接续</a>　<a :href="root+'docs/PLAN_ALIGNMENT.md'" target="_blank" rel="noopener">13份原规划对照</a>　<a :href="root+'docs/WORKBENCH_PLAN.md'" target="_blank" rel="noopener">工作台验收与边界</a></p></section></template>
