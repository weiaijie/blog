<script setup lang="ts">
import {computed,ref} from 'vue';import {market} from '../state';import {names,symbols} from '../domain';import Chart from '../components/Chart.vue';
const symbol=ref('510300');const candles=computed(()=>market.value?.candles[symbol.value]?.map(([date,open,high,low,close])=>({date,open,high,low,close}))||[]);
</script>
<template><div class="page-title"><div><h1>行情与可回测范围</h1><p>有K线不等于可用于收益回测。分红、折算和交易约束还需通过准入。</p></div><label>ETF<select v-model="symbol"><option v-for="s in symbols" :key="s" :value="s">{{names[s]}} · {{s}}</option></select></label></div>
  <section class="panel"><Chart v-if="candles.length" :candles="candles" :height="400" :label="names[symbol]+'未复权日K；不是含分红净值'"/><p v-else>行情正在加载，或数据不可用。</p></section>
  <section class="panel"><h2>逐只核验范围</h2><div class="table-scroll" tabindex="0"><table><thead><tr><th>ETF</th><th>行情起点</th><th>行情截止</th><th>报价日数</th><th>可回测连续区间</th></tr></thead><tbody><tr v-for="(c,s) in market?.coverage" :key="s"><th>{{names[s]}} {{s}}</th><td>{{c.quoteStart}}</td><td>{{c.quoteThrough}}</td><td>{{c.quotes}}</td><td><div v-for="w in c.backtestWindows" :key="w[0]">{{w[0]}} 至 {{w[1]}}</div></td></tr></tbody></table></div><p class="muted">标普ETF 2022-03-29拆分停牌，保留拆分前后两段；不跨缺口强行计算。趋势/因子模型需要起点前的预热行情，可用起点另受限制。</p><a href="/market-data.json" target="_blank" rel="noopener">查看同源行情与覆盖JSON</a></section>
</template>
