<script setup lang="ts">
import {money,pct,names,type Frame,type Signal} from '../domain';
defineProps<{frame:Frame;previous?:Frame}>();
const reasons:Record<string,string>={filled:'已成交',cash_limited:'现金不足',cash_limited_partial_or_zero:'受现金限制',known_ex_dividend_day:'除息日保护',opening_halt:'开盘停牌',conservative_9pct_buffer:'价格保护'};
function signal(p:Signal){return {initial:'首次建仓',monthly:'月初再平衡',installment:'第'+p.batch+' / '+p.installments+'批建仓',trend_on:'120日趋势满足，股债各半',trend_off:'120日趋势未满足，全债',factor_balanced:'基础票数及所需确认满足，股债各半',factor_bonds:'模型条件未满足，全债'}[p.reason]||p.reason;}
</script>
<template>
  <h3>{{frame.date}} · 交易与决策</h3>
  <dl class="stats compact"><div><dt>账户权益</dt><dd>{{money(frame.equity)}} 元</dd></div><div><dt>当天盈亏</dt><dd>{{money(frame.dayPnl)}} 元</dd></div><div><dt>距前高</dt><dd>{{pct(frame.drawdown)}}</dd></div><div><dt>可用现金 / 应收分红</dt><dd>{{money(frame.availableCash)}} / {{money(frame.receivables)}}</dd></div></dl>
  <p>持仓：<span v-for="(units,symbol) in frame.holdings" :key="symbol">{{names[symbol]}} {{units}} 份　</span></p>
  <h4>今天开盘执行</h4><p>{{previous?.nextPlan?previous.date+' 收盘决定：'+signal(previous.nextPlan):'此前没有待执行的新目标。'}}</p>
  <ul v-if="frame.orders.length" class="order-list"><li v-for="(o,i) in frame.orders" :key="i">{{names[o.symbol]}} {{o.side==='buy'?'买入':'卖出'}} {{o.filled}} / 计划 {{o.requested}} 份；模拟价 {{money(o.price)}}，佣金 {{money(o.fee)}} 元。{{reasons[o.reason]||o.reason}}</li></ul><p v-else class="muted">当天没有模拟订单。</p>
  <h4>今天收盘后的决定</h4><p v-if="frame.nextPlan">{{signal(frame.nextPlan)}}；执行日 {{frame.nextPlan.execution}}。目标：<span v-for="(n,s) in frame.nextPlan.target" :key="s">{{names[s]}} {{n}} 份　</span></p><p v-else>当前没有新增执行目标。</p>
  <template v-if="frame.decision"><p>{{frame.decision.votes}} / 3 基础项满足<span v-if="frame.decision.gate">，新增条件{{frame.decision.gate.passed?'满足':'未满足'}}</span>；收盘目标：{{frame.decision.regime==='balanced'?'股债各半':'全债'}}。</p><ul class="factor-list"><li v-for="f in frame.decision.factors" :key="f.key"><strong :class="f.passed?'pass':'fail'">{{f.passed?'满足':'未满足'}} · {{f.label}}</strong><span>{{f.rule}}</span><span>读数 {{f.unit==='raw'?Number(f.value).toFixed(3):pct(f.value)}}</span></li></ul></template>
</template>
