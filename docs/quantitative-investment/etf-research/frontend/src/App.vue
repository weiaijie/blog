<script setup lang="ts">
import {ref,watch} from 'vue';
import {useRoute} from 'vue-router';
import {plan,notice,loadBase,applyPlan} from './state';
import {models,money} from './domain';
import PlanEditor from './components/PlanEditor.vue';
const route=useRoute(),settings=ref(false),error=ref('');
const links=[['/','研究总览'],['/market','行情与数据'],['/research','模型回测'],['/compare','组合比较'],['/reports','研究报告']];
async function init(){error.value='';try{await loadBase();}catch(e){error.value=String((e as Error).message);}}
watch(()=>route.query.plan,raw=>{if(typeof raw==='string'){try{applyPlan(JSON.parse(raw));notice.value='已从链接恢复方案，请运行取得结果。';}catch(e){error.value=(e as Error).message;}}},{immediate:true});
watch(()=>route.meta.title,t=>{document.title=String(t||'量化研究')+' · ETF工作台';},{immediate:true});
function skip(){document.getElementById('main')?.focus();}
init();
</script>
<template>
  <a class="skip" href="#main" @click.prevent="skip">跳到主要内容</a>
  <aside class="sidebar"><a class="brand" href="#/">ETF<span>量化研究工作台</span></a>
    <nav aria-label="主要导航"><RouterLink v-for="[path,label] in links" :key="path" :to="path!" :class="{selected:route.path===path}">{{label}}</RouterLink></nav>
    <div class="sidebar-note">研究与模拟账户<br>人民币 · 含分红口径<br><a href="/backtest.html#replay">旧版完整研究页 ↗</a></div>
  </aside>
  <div class="workspace"><header class="topbar"><div><span class="eyebrow">{{route.meta.title}}</span><strong>{{plan.name}}</strong></div><el-button type="primary" @click="settings=true">研究设置与保存</el-button></header>
    <div class="context-bar"><span>{{plan.start}} — {{plan.end}}</span><span>每户 {{money(plan.capital)}} 元</span><span>{{{low:'低费用',base:'基准费用',high:'高费用'}[plan.fees]}}</span><span>回放：{{models[plan.model]}}</span></div>
    <main id="main" tabindex="-1"><el-alert v-if="error" type="error" :title="error" :closable="false"/><el-button v-if="error" @click="init">重试状态加载</el-button><p v-if="notice" class="notice" role="status">{{notice}}</p><RouterView/></main>
    <footer>仅研究模拟。历史回测与前瞻账户独立；方案保存不会改变18个前瞻账户。行情合格后才能用于计算。</footer>
  </div>
  <el-drawer v-model="settings" title="研究方案" size="min(560px, 100vw)" :close-on-click-modal="false"><PlanEditor @done="settings=false"/></el-drawer>
</template>
