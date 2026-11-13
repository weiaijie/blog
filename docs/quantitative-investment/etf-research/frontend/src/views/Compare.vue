<script setup lang="ts">
import {ref,computed,watch,onBeforeUnmount} from 'vue';
import {plan,getJson,download} from '../state';
import {endpoint as dataEndpoint,apiUrl,parsePlan,comparisonParams,replayParams,models,money,pct,type Plan,type Params,type CompareResult,type Period,type Overlay,type ModelDetail,type Replay,type Backtest,type Windows} from '../domain';
import Chart from '../components/Chart.vue';import AttributionTable from '../components/AttributionTable.vue';import DayDetail from '../components/DayDetail.vue';
const kind=ref('weights'),busy=ref(false),error=ref(''),result=ref<CompareResult>(),pinned=ref<Plan>(),requestUrl=ref(''),detailUrl=ref('');
const overlay=ref<Overlay>(),modelDetail=ref<ModelDetail>(),single=ref<Backtest>(),anchor=ref('A'),pair=ref('B-A'),interval=ref('holding'),day=ref(''),model=ref('allocation'),replay=ref<Replay>(),drawer=ref(false);
let generation=0,controller:AbortController|undefined;
function clearDetail(){overlay.value=undefined;modelDetail.value=undefined;single.value=undefined;replay.value=undefined;day.value='';detailUrl.value='';drawer.value=false;}
function clear(){generation++;controller?.abort();busy.value=false;result.value=undefined;clearDetail();error.value='';requestUrl.value='';}
watch(plan,clear,{deep:true});watch(kind,clear);onBeforeUnmount(clear);
async function request<T>(url:string,consume:(data:T)=>void){const run=++generation;controller?.abort();controller=new AbortController();busy.value=true;error.value='';try{const data=await getJson<T>(url,controller.signal);if(run===generation)consume(data);}catch(e){if(run===generation)error.value=(e as Error).message;}finally{if(run===generation)busy.value=false;}}
function run(){clear();try{const p=parsePlan(plan);pinned.value=p;const endpoint=kind.value==='weights'?(p.portfolios.length===1?'windows':'compare'):kind.value==='methods'?'method-windows':'technical-factors';const params=comparisonParams(p,kind.value);requestUrl.value=apiUrl(dataEndpoint(p,'/'+endpoint),params);if(endpoint==='windows')request<Windows>(requestUrl.value,d=>result.value={parameters:d.parameters,portfolios:[{...d,id:'A'}]});else request<CompareResult>(requestUrl.value,d=>result.value=d);}catch(e){error.value=(e as Error).message;}}
function rows(year:string):{id:string;label:string;period:Period}[]{const r=result.value;if(!r)return [];return r.portfolios?r.portfolios.map(p=>({id:p.id,label:'组合 '+p.id,period:p.periods[year]!})):Object.entries(r.periods?.[year]||{}).map(([id,period])=>({id,label:models[id]||id,period}));}
function openWorst(id:string,p:Period){
  if(!p.worstStart||!p.worstEnd||!pinned.value||!result.value)return;clearDetail();anchor.value=id;interval.value='holding';
  const params={...result.value.parameters,start:p.worstStart,end:p.worstEnd};
  if(kind.value==='weights'){
    if(pinned.value.portfolios.length===1){detailUrl.value=apiUrl(dataEndpoint(pinned.value),params);request<Backtest>(detailUrl.value,d=>{single.value=d;day.value=d.daily.at(-1)!.date;model.value='allocation';});}
    else{detailUrl.value=apiUrl(dataEndpoint(pinned.value,'/overlay'),params);request<Overlay>(detailUrl.value,d=>{overlay.value=d;pair.value=(id==='A'?'B':'A')+'-'+id;day.value=d.portfolios[0]!.daily.at(-1)!.date;model.value='allocation';});}
  }else{detailUrl.value=apiUrl(dataEndpoint(pinned.value,'/'+(kind.value==='methods'?'method-detail':'technical-detail')),params);request<ModelDetail>(detailUrl.value,d=>{modelDetail.value=d;model.value=id;day.value=d.models[id]!.curve.at(-1)!.date;});}
}
const palettes=['#237764','#b66632','#4a64aa','#80649d'];
const curves=computed(()=>overlay.value?.portfolios.map(p=>({id:p.id,points:p.daily}))|| (single.value?[{id:'A',points:single.value.daily}]:Object.entries(modelDetail.value?.models||{}).map(([id,m])=>({id,points:m.curve}))));
const gap=computed(()=>overlay.value?.attribution.dailyGaps[pair.value]);
const lines=computed(()=>{
 const ls=curves.value.flatMap((p,i)=>[{label:(models[p.id]||p.id)+' 权益',color:palettes[i%4]!,points:p.points.map(x=>({date:x.date,value:+x.equity})),pane:0},{label:(models[p.id]||p.id)+' 回撤%',color:palettes[i%4]!,points:p.points.map(x=>({date:x.date,value:+x.drawdown*100})),pane:1}]);
 if(gap.value)ls.push({label:pair.value+' 累计差额',color:'#816087',points:gap.value.days.map(x=>({date:x.date,value:+x.cumulative})),pane:2});return ls;
});
const attribution=computed(()=>{const a=overlay.value?.attribution;return a?(interval.value==='holding'?a.holding:a.peakToTrough[anchor.value]):undefined;});
const gapDay=computed(()=>gap.value?.days.find(x=>x.date===day.value));
const frames=computed(()=>replay.value?.frames||[]);const frame=computed(()=>frames.value.find(f=>f.date===day.value));const previous=computed(()=>frames.value[frames.value.findIndex(f=>f.date===day.value)-1]);
const detailParams=computed(()=>overlay.value?.parameters||single.value?.parameters||modelDetail.value?.parameters);
function choose(date:string){if(curves.value[0]?.points.some(x=>x.date===date))day.value=date;}
function showTrading(){
 const params=detailParams.value,p=pinned.value;if(!params||!p)return;
 const selectedModel=kind.value==='weights'?'allocation':model.value;
 const config:Plan={...p,start:params.start!,end:params.end!,model:selectedModel,portfolios:kind.value==='weights'?[p.portfolios['ABC'.indexOf(anchor.value)]!]:['1,0,0,1']};
 request<Replay>(apiUrl(dataEndpoint(config,'/replay'),replayParams(config,'all')),d=>{replay.value=d;drawer.value=true;});
}
</script>
<template><div class="page-title"><div><h1>同样条件，比较不同选择</h1><p>每个交易日独立建仓，统计满一年、两年的结果；最差一期再用同一段行情对照。</p></div></div>
  <p><RouterLink to="/changes">查看新增9天前后，赚钱次数、4%达标与最差盈亏的变化 →</RouterLink></p>
  <section class="panel"><div class="actions"><label>比较内容<select v-model="kind"><option value="weights">自定义配比（当前1至3套）</option><option value="methods">四种投资方式（境内股债）</option><option value="technical">量价 / KDJ / ADX（境内股债）</option></select></label><el-button type="primary" :loading="busy" @click="run">运行比较</el-button><el-button v-if="result" @click="download('etf-comparison.json',result)">导出结果</el-button></div>
    <p v-if="kind==='weights'" class="muted">固定配比 {{plan.rebalance==='hold'?'建仓后持有':'按月再平衡'}}；这里不使用“回放模型”选择。<span v-for="(w,i) in plan.portfolios" :key="i">{{'ABC'[i]}}：{{w}}　</span>顺序：沪深300、标普500、恒生、国债。</p>
    <p v-else class="muted">{{kind==='methods'?'固定配比、分批、120日趋势、三因子':'三因子基线与量价、KDJ、ADX确认'}}均使用沪深300与国债，忽略自定义配比和回放模型选择。共用日期、本金及费用；趋势/因子按各自固定规则调仓。</p>
    <p v-if="busy" role="status">正在核算，非默认参数可能耗时较长。修改设置或离开页面可取消等待。</p><el-alert v-if="error" type="error" :title="error" :closable="false"/>
    <p v-if="!result&&!busy" class="empty">点击运行，查看不同起点的赚钱次数、年化达到4%的次数与最差盈亏。</p>
    <template v-if="result"><p>本次参数：{{result.parameters.start}} 至 {{result.parameters.end}}，每户 {{money(result.parameters.capital)}} 元。<a :href="requestUrl" target="_blank" rel="noopener">Agent：同一请求JSON</a></p>
      <div v-for="year in ['1','2']" :key="year" class="comparison-block"><h2>持有 {{year}} 年</h2><div class="table-scroll" tabindex="0"><table><thead><tr><th>方案</th><th>满期次数</th><th>赚钱次数</th><th>年化 ≥ 4%</th><th>最差盈亏（元）</th><th>最差区间</th></tr></thead><tbody><tr v-for="r in rows(year)" :key="r.id"><th>{{r.label}}</th><td>{{r.period.count}}</td><td>{{r.period.profitable}}</td><td>{{r.period.reached}}</td><td>{{money(r.period.worstPnl)}}</td><td><button v-if="r.period.count" class="text-button" :disabled="busy" @click="openWorst(r.id,r.period)">{{r.period.worstStart}} 至 {{r.period.worstEnd}}<br>打开同区间对照</button><span v-else>无满期窗口</span></td></tr></tbody></table></div></div>
      <p class="muted">赚钱为到期净盈亏大于0，4%按实际日历天数年化；相邻窗口重叠，不是独立成功概率。</p>
    </template>
  </section>
  <section v-if="curves.length" class="panel"><div class="section-head"><h2>{{models[anchor]||'组合 '+anchor}} 最差一期 · 同区间对照</h2><a :href="detailUrl" target="_blank" rel="noopener">明细JSON</a></div><p>{{detailParams?.start}} 至 {{detailParams?.end}}，各组从相同本金起步。</p>
    <div v-if="overlay||single" class="table-scroll" tabindex="0"><table><thead><tr><th>组合</th><th>到期盈亏</th><th>最大回撤</th><th>收复前高</th></tr></thead><tbody><tr v-for="p in overlay?.portfolios||(single?[{id:'A',summary:single.summary}]:[])" :key="p.id"><th>{{p.id}}</th><td>{{money(p.summary.pnl)}}</td><td>{{pct(p.summary.max_drawdown)}}</td><td>{{+p.summary.max_drawdown===0?'无回撤':p.summary.recovery||'期末未恢复'}}</td></tr></tbody></table></div>
    <label v-if="overlay">差额方向<select v-model="pair"><option v-for="key in Object.keys(overlay.attribution.dailyGaps)" :key="key" :value="key">{{key.replace('-', ' 减 ')}}</option></select></label>
    <Chart :lines="lines" :height="overlay?540:420" label="同区间权益（元）、回撤（%）与累计盈亏差额（元）" @select="choose"/>
    <div class="actions"><label>核对交易日<select v-model="day"><option v-for="r in curves[0]?.points" :key="r.date">{{r.date}}</option></select></label><label v-if="modelDetail">查看模型<select v-model="model"><option v-for="key in Object.keys(modelDetail.models)" :key="key" :value="key">{{models[key]}}</option></select></label><el-button :disabled="busy" @click="showTrading">查看{{kind==='weights'?'所选组合':'模型'}}当日买卖与因子</el-button></div>
    <template v-if="gap"><div class="ranks"><p>差额增加最多：<button v-for="d in gap.increases" :key="d" class="text-button" @click="day=d">{{d}}</button></p><p>差额减少最多：<button v-for="d in gap.decreases" :key="d" class="text-button" @click="day=d">{{d}}</button></p></div><h3>{{day}} · {{pair}} 当日差额 {{money(gapDay?.change)}} 元</h3><p>累计差额 {{money(gapDay?.cumulative)}} 元。各ETF及费用贡献与当日账户差额对账；正值表示前者相对后者贡献更多。</p><AttributionTable v-if="gapDay" :data="gapDay"/>
      <h3>整段盈亏差额</h3><label>统计区间<select v-model="interval"><option value="holding">整个持有期</option><option value="drawdown">所选组合前高至谷底</option></select></label><p>{{attribution?.start}} 至 {{attribution?.end}} · {{pair}}，净贡献合计 {{money(attribution?.differences[pair]?.totals.net)}} 元。</p><AttributionTable v-if="attribution?.differences[pair]" :data="attribution.differences[pair]!"/>
    </template>
  </section>
  <el-drawer v-model="drawer" :title="(kind==='weights'?'组合 '+anchor:models[model])+' · 当日核对'" size="min(700px, 100vw)"><DayDetail v-if="frame" :frame="frame" :previous="previous"/></el-drawer>
</template>
