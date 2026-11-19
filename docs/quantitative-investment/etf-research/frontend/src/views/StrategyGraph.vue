<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import cytoscape from 'cytoscape';
import { agentManifest, parsePlan, type Plan } from '../domain';
import { getJson } from '../state';

interface GraphNode {
  id: string; label: string; kind: 'factor' | 'entry' | 'experiment';
  description?: string; view?: string; url?: string;
}
interface Edge {source: string; target: string; role: string}
interface Catalog {
  entries: {id: string; rule: string; plan: Plan}[];
  graph: {nodes: GraphNode[]; edges: Edge[]};
}
const route = useRoute(), router = useRouter();
const data = ref<Catalog>(), host = ref<HTMLElement>(), error = ref('');
const labels = {factor:'因子',entry:'模型与基准',experiment:'对照实验'};
const selected = computed(() => data.value?.graph.nodes.find(n => n.id === route.query.node)
  ?? data.value?.graph.nodes[0]);
const entry = computed(() => data.value?.entries.find(row => row.id === selected.value?.id));
const links = computed(() => {
  const id = selected.value?.id;
  return (data.value?.graph.edges ?? []).filter(e => e.source === id || e.target === id).map(edge => ({
    edge, node: data.value!.graph.nodes.find(n => n.id === (edge.source === id ? edge.target : edge.source))!
  }));
});
const height = computed(() => Math.max(230, links.value.length * 55 + 24));
let cy: cytoscape.Core | undefined;
let observer: ResizeObserver | undefined;
function choose(id: string) { void router.push({path:'/catalog/graph', query:{node:id}}); }
function draw() {
  if (!cy || !host.value || !selected.value) return;
  const width = host.value.clientWidth;
  const h = height.value, nodeWidth = Math.min(168, width * .42);
  cy.resize();
  const focus = selected.value;
  const nodes = [focus, ...links.value.map(link => link.node)].map((n, i) => ({
    data: {...n, width:nodeWidth}, classes: i ? n.kind : n.kind + ' focus',
    position:{x: i ? width * .75 : width * .25, y: i ? h / 2 + (i - (links.value.length + 1) / 2) * 55 : h / 2}
  }));
  cy.batch(() => {
    cy!.elements().remove();
    cy!.add(nodes);
    cy!.add(links.value.map(({edge}) => ({data:{...edge}})));
  });
}
async function load() {
  error.value = '';
  try {
    const catalog = await getJson<Catalog>('/strategy-catalog.json');
    for (const row of catalog.entries) row.plan = parsePlan(row.plan);
    data.value = catalog;
    await nextTick();
    if (!host.value) return;
    cy = cytoscape({container:host.value, elements:[], layout:{name:'preset'}, autoungrabify:true,
      userZoomingEnabled:false, userPanningEnabled:false, boxSelectionEnabled:false,
      style:[
        {selector:'node',style:{shape:'round-rectangle',width:'data(width)',height:42,label:'data(label)',
          'text-valign':'center','text-halign':'center','font-size':13,'text-wrap':'wrap','text-max-width':'132px',
          'font-family':'sans-serif',color:'#fff','background-color':'#264a60'}},
        {selector:'.factor',style:{'background-color':'#287468'}},
        {selector:'.experiment',style:{'background-color':'#ead8ae',color:'#43341d'}},
        {selector:'.focus',style:{'border-width':3,'border-color':'#0e2c3c'}},
        {selector:'edge',style:{width:1.5,'curve-style':'bezier','line-color':'#93a9ad',
          'target-arrow-shape':'triangle','target-arrow-color':'#81999e'}}
      ]});
    cy.on('tap','node', e => choose(e.target.id()));
    observer = new ResizeObserver(draw);
    observer.observe(host.value);
    draw();
  } catch (e) { error.value=(e as Error).message; }
}
watch(selected,draw,{flush:'post'});
onMounted(load);
onBeforeUnmount(() => { observer?.disconnect(); cy?.destroy(); });
</script>
<template>
  <div class="page-title"><div><h1>策略关系图</h1><p>沿因子找到使用它的模型，再查看对照实验或回放交易。</p></div>
    <RouterLink to="/catalog">返回策略台账</RouterLink></div>
  <el-alert v-if="error" type="error" :title="error" :closable="false"/>
  <el-button v-if="error" @click="load">重新加载</el-button>
  <p v-if="!data && !error" role="status">正在加载关系…</p>
  <div v-if="data && selected" class="graph-grid">
    <section class="panel diagram"><label>定位节点<select :value="selected.id" @change="choose(($event.target as HTMLSelectElement).value)">
      <optgroup v-for="(name,kind) in labels" :key="kind" :label="name">
        <option v-for="n in data.graph.nodes.filter(item=>item.kind===kind)" :key="n.id" :value="n.id">{{n.label}}</option>
      </optgroup></select></label>
      <p class="legend"><span>因子</span><span>模型与基准</span><span>对照实验</span></p>
      <div ref="host" class="canvas" :style="{height:height+'px'}" aria-label="所选节点的直接关系，亦可从相邻节点列表选择"></div>
    </section>
    <section class="panel details" aria-live="polite"><p class="muted">{{labels[selected.kind]}}</p><h2>{{selected.label}}</h2>
      <p>{{entry?.rule ?? selected.description}}</p>
      <div v-if="entry" class="actions"><RouterLink class="primary-link" :to="{path:'/research',query:{plan:JSON.stringify(entry.plan)}}">用报告参数回放</RouterLink>
        <a :href="agentManifest(entry.plan).requests.replay" target="_blank" rel="noopener">Agent 首日请求</a></div>
      <div v-if="selected.kind==='experiment'" class="actions"><a :href="selected.view">打开对照实验</a>
        <a :href="selected.url" target="_blank" rel="noopener">查看 GitHub 报告 ↗</a></div>
      <h3>{{selected.kind==='factor'?'使用这个因子的模型':'相邻节点'}}</h3>
      <ul><li v-for="{node,edge} in links" :key="node.id"><button class="text-button" @click="choose(node.id)">{{node.label}}</button><small>{{edge.role}}</small></li></ul>
      <a href="/strategy-catalog.json" target="_blank" rel="noopener">Agent 关系数据 ↗</a>
    </section>
  </div>
</template>
<style scoped>
.graph-grid{display:grid;grid-template-columns:minmax(0,3fr) minmax(250px,2fr);gap:16px;align-items:start}
.diagram,.details{min-width:0}.canvas{width:100%;background:#f5f8f8;border-radius:5px}
.legend{display:flex;gap:16px;font-size:12px;color:#415a67}.legend span::before{content:'';display:inline-block;width:9px;height:9px;margin-right:5px;background:#287468}.legend span:nth-child(2)::before{background:#264a60}.legend span:nth-child(3)::before{background:#ead8ae}
.details h2{margin-top:0}.details ul{list-style:none;padding:0}.details li{display:flex;align-items:center;justify-content:space-between;gap:8px;border-bottom:1px solid #dfebec}.details small{white-space:nowrap;color:#47616c}.details button{min-height:44px;text-align:left}
@media(max-width:900px){.graph-grid{grid-template-columns:1fr;gap:0}}
</style>
