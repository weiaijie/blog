import { createApp } from 'vue';
import { createRouter, createWebHashHistory } from 'vue-router';
import { ElButton, ElInput, ElInputNumber, ElSelect, ElOption, ElDrawer, ElAlert } from 'element-plus';
import 'element-plus/theme-chalk/base.css';
import 'element-plus/theme-chalk/el-button.css';
import 'element-plus/theme-chalk/el-input.css';
import 'element-plus/theme-chalk/el-input-number.css';
import 'element-plus/theme-chalk/el-select.css';
import 'element-plus/theme-chalk/el-option.css';
import 'element-plus/theme-chalk/el-drawer.css';
import 'element-plus/theme-chalk/el-overlay.css';
import 'element-plus/theme-chalk/el-icon.css';
import 'element-plus/theme-chalk/el-alert.css';
import './style.css';
import App from './App.vue';
const router = createRouter({history:createWebHashHistory(), routes:[
  {path:'/',component:()=>import('./views/Overview.vue'),meta:{title:'研究总览'}},
  {path:'/market',component:()=>import('./views/Market.vue'),meta:{title:'行情与数据'}},
  {path:'/research',component:()=>import('./views/Research.vue'),meta:{title:'模型回测'}},
  {path:'/compare',component:()=>import('./views/Compare.vue'),meta:{title:'组合比较'}},
  {path:'/changes',component:()=>import('./views/DataChanges.vue'),meta:{title:'数据更新对比'}},
  {path:'/changes/attribution',component:()=>import('./views/NewWindows.vue'),meta:{title:'新增两年窗口归因'}},
  {path:'/reports',component:()=>import('./views/Reports.vue'),meta:{title:'研究报告'}},
  {path:'/:pathMatch(.*)*',redirect:'/'},
], scrollBehavior:()=>({top:0})});
const app=createApp(App);
for(const c of [ElButton,ElInput,ElInputNumber,ElSelect,ElOption,ElDrawer,ElAlert]) app.component(c.name!,c);
app.use(router).mount('#app');
