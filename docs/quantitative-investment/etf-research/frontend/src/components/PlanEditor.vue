<script setup lang="ts">
import {ref} from 'vue';
import {plan,savePlan,storedPlans,applyPlan,download,notice,options} from '../state';
import {parsePlan,agentManifest,symbols,names,models,type Plan} from '../domain';
const emit=defineEmits<{done:[]}>();
const error=ref(''),saved=ref<Plan[]>([]),selected=ref(''),link=ref('');
function refresh(){try{saved.value=storedPlans();}catch(e){error.value=(e as Error).message;}}
refresh();
function attempt(fn:()=>void){try{error.value='';fn();}catch(e){error.value=(e as Error).message;}}
function save(){attempt(()=>{savePlan();refresh();notice.value='已保存到当前浏览器；同名方案会更新。可导出JSON带到其他设备。';});}
function restore(){attempt(()=>{const p=saved.value.find(x=>x.name===selected.value);if(p){applyPlan(p);notice.value='已恢复方案，请重新运行。';}});}
const removed=ref<Plan>();
function remove(){attempt(()=>{removed.value=saved.value.find(x=>x.name===selected.value);localStorage.setItem('etf.workbench.plans.v1',JSON.stringify(saved.value.filter(x=>x.name!==selected.value)));refresh();selected.value='';});}
function undo(){attempt(()=>{if(removed.value){const entries=storedPlans();if(entries.length>=20)throw Error('方案列表已满，暂不能恢复。');if(!entries.some(p=>p.name===removed.value!.name))entries.push(removed.value);localStorage.setItem('etf.workbench.plans.v1',JSON.stringify(entries));refresh();removed.value=undefined;}});}
function setWeight(i:number,j:number,value:string){const parts=plan.portfolios[i]!.split(',');parts[j]=value;plan.portfolios[i]=parts.join(',');}
function share(){attempt(()=>{const p=parsePlan(plan);link.value=location.origin+'/workbench/#/research?'+new URLSearchParams({plan:JSON.stringify(p)});});}
async function importFile(e:Event){try{const file=(e.target as HTMLInputElement).files?.[0];if(!file)return;if(file.size>262144)throw Error('方案文件超过256KB。');applyPlan(JSON.parse(await file.text()));error.value='';notice.value='已导入方案，请检查参数后运行。';}catch(e){error.value=(e as Error).message;}finally{(e.target as HTMLInputElement).value='';}}
function done(){attempt(()=>{parsePlan(plan);notice.value='研究设置已应用。已有结果会失效，请重新运行。';emit('done');});}
</script>
<template>
  <p class="muted">本金、日期和费用由回测与比较共用。数据和模型约束仍由服务端核验。</p>
  <el-alert v-if="error" :title="error" type="error" :closable="false"/>
  <form class="settings-form" @submit.prevent="done">
    <label>数据版本<select v-model="plan.dataset" name="dataset"><option value="verified-2026-11-12">近期核验版 · 截至2026-11-12</option><option value="frozen-2026-10-30">原冻结样本 · 截至2026-10-30</option></select></label>
    <p class="muted">旧方案恢复时保留原样本。近期版按公告阻止停牌日开盘成交，不假设10:30补单；原历史报告与前瞻账户独立保留。</p>
    <label>方案名称<input v-model="plan.name" maxlength="80" name="plan-name" autocomplete="off"></label>
    <div class="two-col"><label>开始日期<input v-model="plan.start" type="date" name="start"></label><label>结束日期<input v-model="plan.end" type="date" name="end" :max="plan.dataset==='frozen-2026-10-30'?'2026-10-30':options?.last" ></label></div>
    <div class="two-col"><label>本金（元）<input v-model="plan.capital" type="number" min="1" max="1000000000" step="0.01" name="capital"></label><label>费用与滑点<select v-model="plan.fees" name="fees"><option value="low">低：万一 / 1bp</option><option value="base">基准：万三 / 5bp</option><option value="high">高：千一 / 10bp</option></select></label></div>
    <p class="muted">单边佣金最低5元；滑点单边计入，完整口径与旧版相同。</p>
    <label>固定配比与分批建仓后的调仓<select v-model="plan.rebalance" name="rebalance"><option value="hold">建仓后持有</option><option value="monthly">每月调回目标配比</option></select></label>
    <label>逐日回放模型<select v-model="plan.model" name="model"><option v-for="(label,key) in models" :key="key" :value="key">{{label}}</option></select></label>
    <label>分批期数<input v-model="plan.installments" name="installments" type="number" min="2" max="12" step="1"></label>
    <p class="muted">趋势和多因子固定用沪深300、国债，按各自规则在股债各半与全债之间切换；不会使用下方自定义配比。固定配比和分批回放使用组合A。</p>
    <fieldset v-for="(vector,i) in plan.portfolios" :key="i"><legend>组合 {{'ABC'[i]}}</legend><div class="weights"><label v-for="(symbol,j) in symbols" :key="symbol">{{names[symbol]}}<input :value="vector.split(',')[j]" @input="setWeight(i,j,($event.target as HTMLInputElement).value)" type="number" min="0" max="99999.99" step="0.01" :name="'weight-'+i+'-'+symbol"></label></div><p class="muted">相对配比；1 / 0 / 0 / 1 表示沪深300与国债各50%。</p></fieldset>
    <div class="actions"><el-button v-if="plan.portfolios.length<3" @click="plan.portfolios.push('1,0,0,1')">添加组合</el-button><el-button v-if="plan.portfolios.length>1" @click="plan.portfolios.pop()">移除末组</el-button><el-button type="primary" native-type="submit">应用设置</el-button></div>
  </form>
  <h3>保存与复用</h3><div class="actions"><el-button @click="save">保存到本机</el-button><el-button @click="attempt(()=>download('etf-plan.json',parsePlan(plan)))">导出方案JSON</el-button><el-button @click="share">生成复现链接</el-button></div>
  <label v-if="link">复现链接（含方案参数）<textarea :value="link" readonly rows="4" @focus="($event.target as HTMLTextAreaElement).select()"></textarea></label>
  <label>导入方案JSON<input type="file" accept=".json,application/json" @change="importFile"></label>
  <label>本机已保存方案<select v-model="selected"><option value="">选择方案</option><option v-for="p in saved" :key="p.name">{{p.name}}</option></select></label>
  <div class="actions"><el-button :disabled="!selected" @click="restore">恢复所选方案</el-button><el-button :disabled="!selected" @click="remove">删除所选方案</el-button></div>
  <p v-if="removed" role="status">已删除 {{removed.name}}。<button class="text-button" @click="undo">撤销删除</button></p>
  <h3>Agent使用同一套参数</h3><p class="muted">导出的请求清单明确区分配比回测、所选模型回放和固定模型比较。将相对请求地址加到当前看板地址后即可GET查询；数据不合格会返回错误。</p><el-button @click="attempt(()=>download('etf-agent-requests.json',agentManifest(plan)))">导出Agent请求清单</el-button>
</template>
