<script setup lang="ts">
import {market,loadBase} from '../state';
import {computed,ref} from 'vue';
import {money} from '../domain';
import Chart from '../components/Chart.vue';
const lines=computed(()=>[{label:'前瞻权益（元）',color:'#237764',points:market.value?.curve.map(([date,value])=>({date,value}))||[]}]);
const error=ref(''),refreshing=ref(false);
async function refresh(){refreshing.value=true;error.value='';try{await loadBase(true);}catch(e){error.value=(e as Error).message;}finally{refreshing.value=false;}}
</script>
<template><div class="page-title"><div><h1>研究进度与模拟账户</h1><p>配置模型，逐日走行情；看清什么时候交易，以及收益从哪里来。</p></div><RouterLink class="primary-link" to="/research">进入模型回测</RouterLink></div>
  <section class="panel"><div class="section-head"><h2>当前数据与观察进度</h2><el-button :loading="refreshing" @click="refresh">刷新状态</el-button></div><el-alert v-if="error" :title="error" type="error" :closable="false"/>
    <dl v-if="market" class="stats"><div><dt>前瞻账户截止</dt><dd>{{market.asOf}}</dd></div><div><dt>真正前瞻观察</dt><dd>{{market.sessions}} 个交易日</dd></div><div><dt>月度50/50权益</dt><dd>{{money(market.curve.at(-1)?.[1])}} 元</dd></div><div><dt>历史回测截止</dt><dd>{{market.coverage['510300']?.backtestWindows.at(-1)?.[1]}}</dd></div></dl>
    <p class="muted">此处权益仅展示18户中的月度50/50基准账户。前瞻从2026-11-05开始，不把历史回测接入前瞻收益，样本不足不展示前瞻年化。</p>
    <Chart v-if="market" :lines="lines" :height="250" label="独立前瞻模拟账户权益"/>
  </section>
  <div class="two-col"><section class="panel"><h2>你现在可以做</h2><ol class="workflow"><li><RouterLink to="/research">配置并逐日回放</RouterLink><span>固定配比、分批、趋势和多因子，看到收盘决策与次日成交。</span></li><li><RouterLink to="/compare">比较组合与投资方式</RouterLink><span>同本金、日期和费用，统计一年/两年结果，打开最差一期。</span></li><li><RouterLink to="/reports">查研究结论与证据</RouterLink><span>ADX、纯债、交易成本和逐日归因；固定报告与当前方案分开。</span></li></ol></section>
    <section class="panel"><h2>还不能下的结论</h2><p>模型长期年化4%～5%是否可行，仍需要一至两年的前瞻观察。历史窗口大量重叠，赚钱次数不是未来成功概率。</p><p>ADX最近的两年对照中，746期胜纯债、616期落后；其中321期加回费用仍落后。复杂模型尚未证明稳定胜过简单配置。</p><p>完整停复牌、部分正式除息参考价、全持仓穿透及真实成交仍有证据缺口。</p></section></div>
</template>
