(() => {
  const {h} = Vue;
  const legs = {allocation:'一次建仓', installments:'按月分批', difference:'分批减一次'};
  const etfs = {'510300':'沪深300', '511010':'国债'};
  const parts = {price:'价格', dividend:'分红', commission:'佣金', slippage:'滑点', net:'合计'};
  const money = value => Number(value).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  const quote = value => value == null ? '—' : Number(value).toFixed(3);
  function partsTable(rows) {
    return h('div',{class:'method-scroll'},h('table',[
      h('thead',h('tr',['项目（元）',...Object.values(parts)].map(label=>h('th',{scope:'col'},label)))),
      h('tbody',rows.map(([label,values])=>h('tr',[
        h('th',{scope:'row'},label),...Object.entries(parts).map(([key,title])=>h('td',{'data-label':title},money(values[key])))
      ])))
    ]));
  }
  window.MethodGap = {
    props:{params:{type:Object,required:true}},
    data:()=>({report:null,selected:'',error:''}),
    computed:{
      url() {return 'api/v1/backtest/method-gap?'+new URLSearchParams(this.params);},
      byDate() {return new Map(this.report?.days.map(row=>[row.date,row]));}
    },
    async mounted() {
      const controller = new AbortController();
      this.cancelFetch = ()=>controller.abort();
      try {
        const res = await fetch(this.url,{signal:controller.signal});
        const data = await res.json();
        if (!res.ok) throw Error(data.error||'逐日对账暂时不可用。');
        this.report = data;
        this.selected = data.worsening[0] || data.start;
        await this.$nextTick();
        if (!controller.signal.aborted) this.draw();
      } catch(e) {if (!controller.signal.aborted) this.error=e.message;}
    },
    beforeUnmount() {this.cancelFetch?.();this.removeChart?.();},
    methods:{
      draw() {
        const chart = LightweightCharts.createChart(this.$refs.chart,{autoSize:true,handleScroll:false,
          layout:{attributionLogo:true},rightPriceScale:{scaleMargins:{top:.24,bottom:.15}}});
        this.removeChart = ()=>chart.remove();
        const line = chart.addSeries(LightweightCharts.LineSeries,{color:'#296856',lineWidth:2,priceLineVisible:false});
        line.setData(this.report.days.map(d=>({time:d.date,value:Number(d.cumulative)})));
        line.createPriceLine({price:0,color:'#75817e',lineWidth:1,lineStyle:2,axisLabelVisible:false});
        LightweightCharts.createSeriesMarkers(line,this.report.widening.map((date,i)=>({
          time:date,position:i%2?'belowBar':'aboveBar',color:'#974f23',shape:'circle',text:'扩大 '+(i+1)
        })).sort((a,b)=>a.time.localeCompare(b.time)));
        chart.timeScale().fitContent();
        chart.subscribeClick(({time})=>{if(this.byDate.has(time)) this.selected=time;});
      },
      ranks(title,key,metric) {
        const dates=this.report[key];
        return h('div',{class:'method-gap-ranks'},[h('strong',title),...dates.map(date=>h('button',{
          type:'button','aria-pressed':this.selected===date,onClick:()=>{this.selected=date;}
        },date+' · '+money(this.byDate.get(date)[metric])+' 元')),dates.length?'':'无']);
      }
    },
    render() {
      if (!this.report) return h('p',{role:'status'},this.error||'正在逐日核对持仓和权益…');
      const r=this.report, day=this.byDate.get(this.selected);
      return h('section',{class:'method-gap'},[
        h('h4','分批减一次建仓 · 累计盈亏差额'),
        h('p',r.start+' 至 '+r.end+'，一次建仓盈亏 '+money(r.accounts.allocation.pnl)+' 元，分 '+r.parameters.installments+' 批盈亏 '+money(r.accounts.installments.pnl)+' 元，相差 '+money(r.totals.net)+' 元。'),
        partsTable([...Object.entries(etfs).map(([s,title])=>[title+' '+s,r.byEtf[s]]),['全期差额',r.totals]]),
        h('div',{ref:'chart',class:'method-gap-chart',role:'img','aria-label':'分批减一次建仓累计盈亏差额（元），圆点标出绝对差距扩大最多的三个交易日'}),
        h('p','曲线高于零表示分批领先，低于零表示分批落后。点图或选择日期可核对当天的持仓和盈亏。'),
        this.ranks('两户差距扩大最多（绝对值）','widening','widthChange'),
        this.ranks('分批相对表现下降最多','worsening','change'),
        h('label',['核对交易日 ',h('select',{value:this.selected,onChange:e=>{this.selected=e.target.value;}},r.days.map(d=>h('option',{value:d.date},d.date)))]),
        h('p',{class:'method-gap-day','aria-live':'polite'},day.date+'　当天差额 '+money(day.change)+' 元，累计 '+money(day.cumulative)+' 元。收盘权益：一次 '+money(day.equity.allocation)+' 元，分批 '+money(day.equity.installments)+' 元。'),
        ...Object.entries(etfs).flatMap(([s,title])=>{
          const a=day.assets[s];
          return [h('h5',title+' ETF · '+s),h('p','前收 '+quote(a.previousClose)+'，开盘 '+quote(a.open)+'，收盘 '+quote(a.close)+' 元。'),
            h('p','开盘成交前 → 收盘持仓（份）：一次 '+a.allocation.before+' → '+a.allocation.after+'，分批 '+a.installments.before+' → '+a.installments.after+'。'),
            partsTable(Object.entries(legs).map(([k,label])=>[label,a[k]]))];
        }),
        h('a',{href:this.url},'Agent · 本区间逐日持仓与盈亏差额 JSON'),
        this.error?h('p',{role:'alert'},this.error):null
      ]);
    }
  };
})();
