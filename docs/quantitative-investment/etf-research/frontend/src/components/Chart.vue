<script setup lang="ts">
import {ref,onMounted,onBeforeUnmount,watch} from 'vue';
import {createChart,LineSeries,CandlestickSeries,createSeriesMarkers,type IChartApi,type Time} from 'lightweight-charts';
export interface Line {label:string;color:string;points:{date:string;value:number}[];pane?:number}
const props=withDefaults(defineProps<{lines?:Line[];candles?:{date:string;open:number;high:number;low:number;close:number}[];markers?:{date:string;buy:boolean}[];height?:number;label:string}>(),{height:340});
const emit=defineEmits<{select:[date:string]}>();const host=ref<HTMLElement>();let chart:IChartApi|undefined;
function render(){if(!host.value)return;chart?.remove();chart=createChart(host.value,{autoSize:true,layout:{background:{color:'#ffffff'},textColor:'#405869',attributionLogo:true},grid:{vertLines:{visible:false},horzLines:{color:'#edf1f4'}},localization:{locale:'zh-CN'},timeScale:{borderColor:'#dce4e9'},rightPriceScale:{borderColor:'#dce4e9'}});
  if(props.candles){const s=chart.addSeries(CandlestickSeries,{upColor:'#bd493f',downColor:'#237764',wickUpColor:'#bd493f',wickDownColor:'#237764',borderVisible:false,priceFormat:{type:'price',precision:3,minMove:.001}});s.setData(props.candles.map(p=>({...p,time:p.date as Time})));if(props.markers)createSeriesMarkers(s,props.markers.map(m=>({time:m.date as Time,position:m.buy?'belowBar':'aboveBar',shape:m.buy?'arrowUp':'arrowDown',color:m.buy?'#bd493f':'#237764',text:m.buy?'买':'卖'})));}
  for(const l of props.lines||[]){const s=chart.addSeries(LineSeries,{title:l.label,color:l.color,lineWidth:2,priceLineVisible:false,lastValueVisible:false},l.pane||0);s.setData(l.points.map(p=>({time:p.date as Time,value:p.value})));}
  chart.timeScale().fitContent();chart.subscribeClick(e=>{if(typeof e.time==='string')emit('select',e.time);});
}
onMounted(render);watch(()=>[props.lines,props.candles,props.markers],render);onBeforeUnmount(()=>chart?.remove());
</script>
<template><div ref="host" class="chart" :style="{height:height+'px'}" role="img" :aria-label="label"></div><p class="chart-caption">{{label}} · <a href="https://www.tradingview.com/" target="_blank" rel="noopener noreferrer">图表由 TradingView Lightweight Charts 提供</a></p></template>
