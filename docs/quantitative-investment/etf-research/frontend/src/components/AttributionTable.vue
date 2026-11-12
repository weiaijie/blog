<script setup lang="ts">
import {names,money,type Attribution} from '../domain';
defineProps<{data:Attribution}>();
const columns=['price','dividend','commission','slippage','net'] as const;
</script>
<template><div class="table-scroll" tabindex="0"><table><thead><tr><th>ETF</th><th>价格贡献</th><th>分红</th><th>佣金贡献</th><th>滑点贡献</th><th>净贡献</th></tr></thead><tbody><tr v-for="(parts,s) in data.byEtf" :key="s"><th>{{names[s]}} {{s}}</th><td v-for="c in columns" :key="c">{{money(parts[c])}}</td></tr></tbody><tfoot><tr><th>合计（元）</th><td v-for="c in columns" :key="c">{{money(data.totals[c])}}</td></tr></tfoot></table></div></template>
