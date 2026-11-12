<script setup lang="ts">
import {ref,computed,watch,onBeforeUnmount} from 'vue';
import {plan,getJson,download} from '../state';
import {parsePlan,replayParams,apiUrl,money,pct,names,models,type Replay,type Frame} from '../domain';
import Chart from '../components/Chart.vue';import DayDetail from '../components/DayDetail.vue';
const data=ref<Replay>(),shown=ref(0),selected=ref(''),symbol=ref('510300'),error=ref(''),busy=ref(false),auto=ref(false),url=ref('');let controller:AbortController|undefined;let generation=0;
const visible=computed(()=>data.value?.frames.slice(0,shown.value)||[]);
const last=computed(()=>visible.value.at(-1));
const day=computed(()=>visible.value.find(x=>x.date===selected.value)||last.value);
const previous=computed(()=>{const i=visible.value.findIndex(x=>x.date===day.value?.date);return visible.value[i-1];});
const candles=computed(()=>visible.value.filter(f=>f.bars[symbol.value]).map(f=>({date:f.date,open:+f.bars[symbol.value]!.open,high:+f.bars[symbol.value]!.high,low:+f.bars[symbol.value]!.low,close:+f.bars[symbol.value]!.close})));
const markers=computed(()=>visible.value.flatMap(f=>f.orders.filter(o=>o.symbol===symbol.value&&o.filled>0).map(o=>({date:f.date,buy:o.side==='buy'}))));
const lines=computed(()=>[{label:'权益（元）',color:'#237764',points:visible.value.map(f=>({date:f.date,value:+f.equity}))},{label:'回撤（%）',color:'#b45845',pane:1,points:visible.value.map(f=>({date:f.date,value:+f.drawdown*100}))}]);
function clear(){generation++;controller?.abort();auto.value=false;busy.value=false;data.value=undefined;shown.value=0;selected.value='';url.value='';error.value='';}
watch(plan,clear,{deep:true});onBeforeUnmount(clear);
async function load(step:string){
  auto.value=auto.value&&step!=='all';const run=++generation;controller?.abort();controller=new AbortController();busy.value=true;error.value='';
  try{const p=parsePlan(plan),request=apiUrl('/api/v1/backtest/replay',replayParams(p,step));const result=await getJson<Replay>(request,controller.signal);if(run!==generation)return false;data.value=result;shown.value=result.step;url.value=request;selected.value=result.frames.at(-1)!.date;if(!result.frames[0]!.bars[symbol.value])symbol.value=Object.keys(result.frames[0]!.bars)[0]!;return true;}
  catch(e){if(run===generation){error.value=(e as Error).message;auto.value=false;}return false;}
  finally{if(run===generation)busy.value=false;}
}
async function autoplay(){if(auto.value){auto.value=false;return;}auto.value=true;while(auto.value&&shown.value<(data.value?.totalSessions||0)){if(!await load(String(shown.value+1)))break;await new Promise(r=>setTimeout(r,220));}auto.value=false;}
function choose(date:string){if(visible.value.some(x=>x.date===date))selected.value=date;}
const rules=computed(()=>plan.model==='allocation'?'按组合A配比生成目标；是否按月再平衡取决于方案设置。':plan.model==='installments'?'按月分'+plan.installments+'批投入组合A；批次按原模型执行。':plan.model==='trend_120'?'沪深300含分红指数高于120日均线时股债各半，否则全债。':'趋势、股债相对强弱、波动三项至少两项满足；带量价/KDJ/ADX的版本还需对应确认条件。满足时股债各半，否则全债。');
</script>
<template><div class="page-title"><div><h1>{{models[plan.model]}} · 模型回测</h1><p>{{rules}}</p></div></div>
  <section class="panel"><div class="actions"><el-button type="primary" :disabled="busy||auto" @click="clear();load('1')">从第一天开始</el-button><el-button :disabled="!data||busy||auto||shown>=data.totalSessions" @click="load(String(shown+1))">下一交易日</el-button><el-button :disabled="!data||(!auto&&busy)||shown>=(data?.totalSessions||0)" @click="autoplay">{{auto?'暂停':'逐日自动播放'}}</el-button><el-button :disabled="busy||auto" @click="load('all')">计算完整区间</el-button><el-button v-if="data" @click="download('etf-replay-result.json',data)">导出结果</el-button></div>
    <p role="status" class="muted">{{busy?'正在计算，请稍候…':data?`已展示 ${shown} / ${data.totalSessions} 个交易日`:'尚未运行。逐日回放只请求截至当前步的数据。'}} 收盘形成决策，下一交易日开盘模拟执行。</p><el-alert v-if="error" :title="error" type="error" :closable="false"/>
    <p v-if="!data" class="empty">先打开右上角“研究设置与保存”，确认日期、费用和模型。点“从第一天开始”，就能看到模型在当时知道什么、决定什么。</p>
    <template v-if="data&&last"><dl class="stats"><div><dt>已走到</dt><dd>{{last.date}}</dd></div><div><dt>账户权益</dt><dd>{{money(last.equity)}} 元</dd></div><div><dt>累计盈亏</dt><dd>{{money(last.pnl)}} 元</dd></div><div><dt>当前回撤</dt><dd>{{pct(last.drawdown)}}</dd></div></dl>
    <div class="actions"><label>查看ETF<select v-model="symbol"><option v-for="s in Object.keys(last.bars)" :key="s" :value="s">{{names[s]}} {{s}}</option></select></label><label>查看已走过的交易日<select v-model="selected"><option v-for="f in visible" :key="f.date">{{f.date}}</option></select></label><a :href="url" target="_blank" rel="noopener">Agent：当前请求JSON</a></div>
    <Chart :candles="candles" :markers="markers" label="已走过的日K与模拟买卖；点击日期查看交易" @select="choose"/>
    <Chart :lines="lines" :height="350" label="账户权益与收盘回撤；上方元，下方百分比" @select="choose"/>
    </template>
  </section><section v-if="day" class="panel" aria-live="polite"><DayDetail :frame="day" :previous="previous"/></section>
</template>
