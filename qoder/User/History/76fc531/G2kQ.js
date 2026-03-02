import '@/libs/page-config'

import Vue from 'vue'

// import Cookies from 'js-cookie'

import 'normalize.css/normalize.css' // a modern alternative to CSS resets

import Element from 'element-ui'
import './styles/element-variables.scss'
import './styles/display.css'

import '@/styles/index.scss' // global css

import Print from 'vue-print-nb'
Vue.use(Print)

import App from './App'
import store from './store'
import router from './router'

import i18n from './lang' // internationalization
import './icons' // icon
import './permission' // permission control
import './utils/error-log' // error log

import * as filters from './filters' // global filters

import ComponentRegister from './libs/register'
import Core from './libs/core'
import DragDialog from '@/directive/el-drag-dialog'

// import adaptive from '@/directive/el-table'
import clipboard from '@/directive/clipboard'
import permission from '@/directive/permission'

import FocusSelectInput from '@/directive/el-focus-select-input'

import ECharts from 'vue-echarts'
import { use } from 'echarts/core'

import {
  CanvasRenderer
} from 'echarts/renderers'

import {
  LineChart,
  PieChart
} from 'echarts/charts'

import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  ToolboxComponent
} from 'echarts/components'

if (!Vue.prototype.$bus) {
  Vue.prototype.$bus = new Vue()
}

use([
  LegendComponent, TooltipComponent, TitleComponent, GridComponent, ToolboxComponent,
  CanvasRenderer,
  PieChart, LineChart])
Vue.component('echarts', ECharts)

/**
 * If you don't want to use mock-server
 * you want to use MockJs for mock api
 * you can execute: mockXHR()
 *
 * Currently MockJs will be used in the production environment,
 * please remove it before going online ! ! !
 */
if (process.env.NODE_ENV === 'production') {
  const { mockXHR } = require('../mock')
  mockXHR()
}

Vue.use(DragDialog)

// Vue.use(adaptive)
Vue.use(clipboard)
Vue.use(permission)
Vue.use(FocusSelectInput)

Vue.use(Element, {
  size: 'small' // set element-ui default size
  // i18n: (key, value) => i18n.t(key, value)
})

// register global utility filters
Object.keys(filters).forEach(key => {
  Vue.filter(key, filters[key])
})

ComponentRegister(Vue)

Vue.use(Core)

Vue.config.productionTip = false

new Vue({
  el: '#app',
  router,
  store,
  i18n,
  mounted() {
    document.querySelector('#pageLoading').style.display = 'none'
  },
  render: h => h(App)
})

// 获取服务端定义的类型枚举，需要的时候放开获取一次复制替换/src/libs/common-data.js的FULL_STATUS
import { getEnumMappingValueTypes } from '@/api/gens-api/base-support'
getEnumMappingValueTypes()
