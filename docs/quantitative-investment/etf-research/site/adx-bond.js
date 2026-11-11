(() => {
  const {createApp,h,nextTick}=Vue;
  const ADX='multifactor_adx_v1';
  const money=x=>Number(x).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  const pct=x=>(100*Number(x)).toFixed(2)+'%';
  const colors=['#705a91','#42786a','#b4794c'];
  function table(head,rows) {
    return h('div',{class:'factor-table'},h('table',{class:head.length===2?'adx-parts':''},[
      h('thead',h('tr',head.map(x=>h('th',{scope:'col'},x)))),
      h('tbody',rows.map(row=>h('tr',row.map((x,i)=>h(i?'td':'th',i?{'data-label':head[i]}:{scope:'row'},x)))))
    ]));
  }
  createApp({
    data:()=>({params:null,report:null,detail:null,status:'',busy:false,request:null,horizon:'2',anchor:0,day:'',summaryUrl:'',detailUrl:'',title:''}),
    async mounted(){
      try {
        const r=await fetch('api/v1/backtest/options');if(!r.ok)throw Error('参数暂时不可用');
        this.params=(await r.json()).adxBondDefaults;await this.calculate();
      }catch(e){this.status=e.message;}
    },
    beforeUnmount(){this.request?.abort();this.destroyCharts();},
    methods:{
      destroyCharts(){for(const c of this.charts||[])c.remove();this.charts=[];},
      clear(){this.request?.abort();this.request=null;this.busy=false;this.report=this.detail=null;this.status='';this.destroyCharts();},
      async query(path,params,c) {
        const url='api/v1/backtest/'+path+'?'+new URLSearchParams(params);
        const r=await fetch(url,{signal:c.signal}),data=await r.json();
        if(!r.ok)throw Error(data.error||'研究数据不可用');return {data,url};
      },
      async calculate(){
        this.clear();const c=new AbortController();this.request=c;this.busy=true;this.status='正在核对同日起点账户；自定义参数可能需要几分钟…';
        try {
          const r=await this.query('adx-bond',{...this.params},c);
          if(this.request!==c)return;this.report=r.data;this.summaryUrl=r.url;this.anchor=0;this.status='';
        }catch(e){if(this.request===c&&e.name!=='AbortError')this.status=e.message;}
        finally{if(this.request===c){this.busy=false;this.request=null;}}
      },
      async open(row,title,year=null){
        this.request?.abort();const c=new AbortController();this.request=c;this.busy=true;this.detail=null;this.destroyCharts();
        this.title=title;this.status='正在重放三个账户并逐日对账…';
        const params=year?{...this.report.parameters,year:String(year)}:{...this.report.parameters,start:row.start,end:row.end};
        try {
          const r=await this.query('adx-bond-detail',params,c);
          if(this.request!==c)return;
          if(Math.abs(Number(r.data.summary.gap)-Number(row.gap))>0.000001)throw Error('重放与归档差额不符。');
          this.detail=r.data;this.detailUrl=r.url;
          const ranked=[...r.data.daily].sort((a,b)=>Math.abs(Number(b.gap))-Math.abs(Number(a.gap)));
          this.day=ranked[0]?.date||'';this.status='';
          await nextTick();this.paint();document.getElementById('adx-drill').scrollIntoView({block:'start'});
        }catch(e){if(this.request===c&&e.name!=='AbortError')this.status=e.message;}
        finally{if(this.request===c){this.busy=false;this.request=null;}}
      },
      paint(){
        this.destroyCharts();
        for(const [id,key] of [['adx-nav','nav'],['adx-dd','drawdown']]) {
          const c=LightweightCharts.createChart(document.getElementById(id),{autoSize:true,height:230,
            layout:{background:{color:'#fff'},textColor:'#40574f'},rightPriceScale:{borderVisible:false}});
          Object.entries(this.detail.curves).forEach(([m,rows],i)=>{
            const s=c.addSeries(LightweightCharts.LineSeries,{color:colors[i],title:this.report.models[m],lineWidth:2,
              priceFormat:key==='drawdown'?{type:'percent'}:{type:'price',precision:4,minMove:.0001}});
            s.setData(rows.map(r=>({time:r.date,value:Number(r[key])*(key==='drawdown'?100:1)})));
          });
          c.timeScale().fitContent();c.subscribeClick(p=>{if(typeof p.time==='string')this.day=p.time;});this.charts.push(c);
        }
      },
      etfTable(parts){
        return table(['ETF贡献差','价格','分红','佣金','滑点'],['510300','511010'].map(s=>[s==='510300'?'沪深300':'国债',...['price','dividend','commission','slippage'].map(k=>money(parts[s][k]))]));
      },
      math(row){
        return [
          h('p','实际平均股票敞口 '+pct(row.meanStockWeight)+'；持股时段及调仓日日内贡献扣额外费用、滑点后 '+money(row.timingAfterCosts)+' 元。平均敞口来自本期完整历史，只用于事后解释。'),
          table(['相对纯国债的分项','贡献（元）'],[...Object.keys(this.report.mathLabels).map(k=>[this.report.mathLabels[k],money(row.components[k])]),['与账户核对合计',money(row.gap)]]),
          h('details',[h('summary','按 ETF 核对同一笔纯债差额'),this.etfTable(row.attribution.differences[ADX+'-bonds'].byEtf),h('p','这是同一差额的另一种拆法，不与上表重复相加。')]),
          h('details',[h('summary','相对一次建仓股债各半：下跌日少亏与上涨日少赚分别是多少'),
            h('p','按股票含分红日收益的正负分类。上涨与下跌项往往很大且互相抵消，不是额外赚到的钱；应同时看净合计和成本。'),
            table(['分项','贡献（元）'],[...Object.entries(row.riskComponents).map(([k,v])=>[this.report.riskLabels[k],money(v)]),['与股债各半账户差额',money(row.gapBalanced)]])])
        ];
      }
    },
    render(){
      const nodes=[h('h3','ADX 是否胜过纯国债'),
        h('p','同日起点、同本金、同费用。与纯国债比较是否增加净收益；与一次建仓股债各半比较是否减少股票下跌损失。原规则：基础三因子至少两票，且 ADX ≥ 25、+DI > −DI，才目标股债各半；否则全债。')];
      if(this.params){
        const field=(k,label,type)=>h('label',[label,h('input',{type,value:this.params[k],required:true,
          ...(type==='date'?{min:'2019-03-20',max:'2026-10-30'}:{min:1,max:1e9,step:'.01'}),
          onInput:e=>{this.params[k]=e.target.value;this.clear();}})]);
        nodes.push(h('form',{onSubmit:e=>{e.preventDefault();this.calculate();}},[
          h('div',{class:'work-fields'},[field('start','对照开始日期','date'),field('end','对照结束日期','date'),field('capital','每户本金（元）','number'),
            h('label',['费用方案',h('select',{value:this.params.fees,onChange:e=>{this.params.fees=e.target.value;this.clear();}},
              [['base','基准费用'],['low','低费用'],['high','高费用']].map(([value,label])=>h('option',{value},label)))])]),
          h('button',{type:'submit',disabled:this.busy},'运行 ADX 与纯债对照')]));
      }
      nodes.push(h('p',{role:'status'},this.status));if(!this.report)return nodes;
      const r=this.report,models=Object.keys(r.models),s=r.periods[this.horizon];
      nodes.push(h('label',['持有期',h('select',{id:'adx-horizon',value:this.horizon,onChange:e=>{this.horizon=e.target.value;this.anchor=0;}},
        [h('option',{value:'1'},'1 年'),h('option',{value:'2'},'2 年')])]),
        h('p',{class:'adx-key'},s.count+' 个满期起点：ADX 比纯国债赚得多 '+s.beatBonds+' 次、少 '+s.lagBonds+' 次、持平 '+s.tieBonds+' 次。'),
        table(['账户','赚钱次数','年化 ≥ 4% 次数','最差到期盈亏','回放'],models.map(m=>{
          const a=s.models[m],row=r.windows.find(w=>String(w.years)===this.horizon&&w.start===a.worstStart);
          return [r.models[m],String(a.profitable),String(a.reached),a.count?money(a.worstPnl)+' 元':'—',
            row?h('button',{disabled:this.busy,onClick:()=>this.open(row,r.models[m]+'最差一期')},'看最差一期'):'无满期窗口'];
        })),
        h('p','扣除额外费用后，“持股时段＋调仓日日内贡献”为正的有 '+s.positiveTimingAfterCosts+' 次。此计数依赖本页的事后分解，不是经统计检验的择时成功率。'),
        s.worstGap?h('button',{disabled:this.busy,onClick:()=>this.open(s.worstGap,'ADX 相对纯债落后最多的一期')},'看相对纯债落后最多的一期'):null,
        h('p',{class:'muted'},'全部逐日起点相互重叠；下面另列逐年及不重叠区间，不把重叠窗口当作独立成功概率。'),
        h('h4','完整所选区间 · 收益差从哪里来'),
        table(['账户','到期盈亏','最大收盘回撤','持有股票日数'],models.map(m=>{const a=r.fullPeriod.accounts[m];return [r.models[m],money(a.pnl),pct(a.maxDrawdown),a.stockHoldingDays+' / '+a.observations];})),
        ...this.math(r.fullPeriod),
        h('button',{disabled:this.busy,onClick:()=>this.open(r.fullPeriod,'完整所选区间')},'看完整区间曲线与逐日分解'),
        h('h4','按日历年核对 · 连续账户，不在年初重置'),
        table(['年度','ADX收益','纯债收益','股债各半收益','明细'],r.calendarYears.map(y=>[
          y.year+(y.complete?'':'（不完整）'),pct(y.accounts[ADX].totalReturn),pct(y.accounts.bonds.totalReturn),pct(y.accounts.balanced.totalReturn),
          h('button',{disabled:this.busy,onClick:()=>this.open(y,y.year+' 年连续账户',y.year)},'看该年持仓')])),
        h('p','每年以前一观测年末收盘为锚。年度开始时三个账户的金额可能不同；图中按各自期初归一，收益率可比，金额差按各账户实际余额计算。'),
        h('details',[h('summary','按回测起点年份分组（每个窗口重新从现金建仓）'),
          table(['起点年','满期数','ADX胜纯债','ADX年化≥4%','纯债年化≥4%'],Object.entries(r.entryYears[this.horizon]).map(([year,a])=>[year,String(a.count),String(a.beatBonds),String(a.models[ADX].reached),String(a.models.bonds.reached)]))]),
        h('h4','不重叠区间 · 每期重新投入相同本金'),
        h('p','同一条链内，上一期终点收盘也是下一期起点，收益日不重叠；尾部不足满期不计。不同锚点的链相互重叠，不能合并计数。'));
      const chains=r.nonOverlapping[this.horizon],chain=chains[this.anchor];
      nodes.push(table(['起始锚点','完整区间数','ADX胜 / 负 / 平纯债','ADX赚钱 / 纯债赚钱'],chains.map(c=>[c.anchor,String(c.summary.count),
        c.summary.beatBonds+' / '+c.summary.lagBonds+' / '+c.summary.tieBonds,c.summary.models[ADX].profitable+' / '+c.summary.models.bonds.profitable])),
        h('label',['查看哪条链',h('select',{id:'adx-anchor',value:String(this.anchor),onChange:e=>{this.anchor=Number(e.target.value);}},
          chains.map((c,i)=>h('option',{value:String(i)},c.anchor+(i===0?' · 默认锚点':''))))]));
      if(chain)nodes.push(table(['区间','ADX盈亏','纯债盈亏','差额','回放'],chain.windows.map(w=>[
        w.start+' → '+w.end,money(Number(w.equities[ADX])-Number(r.parameters.capital)),money(Number(w.equities.bonds)-Number(r.parameters.capital)),money(w.gap),
        h('button',{disabled:this.busy,onClick:()=>this.open(w,'不重叠区间')},'看这一期')])),
        h('p',chain.immatureTail?'未满期尾段：'+chain.immatureTail.start+' 至 '+chain.immatureTail.end+'，未计入上述次数。':'无未满期尾段。'));
      nodes.push(h('a',{href:this.summaryUrl},'Agent · 同参数全部窗口、年份和分解 JSON'));
      if(this.detail){
        const d=this.detail,day=d.daily.find(x=>x.date===this.day),a=d.summary;
        nodes.push(h('section',{id:'adx-drill'},[
          h('h4',this.title+' · '+a.start+' 至 '+a.end),
          h('p',d.mode==='continuous_year'?'保留此前账户持仓和净值，下面是所选日历年的持续账户。':'本期三户均从现金起步；分红、整手与执行保护一致。'),
          table(['账户','期初资产','本期盈亏','本期收益','最大回撤'],models.map(m=>{const x=a.accounts[m];return [r.models[m],money(x.startingEquity),money(x.pnl),pct(x.totalReturn),pct(x.maxDrawdown)];})),
          h('p','上图为各自期初归一净值，下图为区间内收盘回撤。点击图中日期可看当日贡献。'),
          h('div',{id:'adx-nav',class:'adx-chart'}),h('div',{id:'adx-dd',class:'adx-chart'}),
          ...this.math(a),
          h('label',['逐日核对',h('select',{id:'adx-day',value:this.day,onChange:e=>{this.day=e.target.value;}},
            [...(!d.daily.some(x=>x.date===this.day)?[h('option',{value:this.day},this.day+' · 起始收盘')]:[]),...d.daily.map(x=>h('option',{value:x.date},x.date+' · 差额变化 '+money(x.gap)+' 元'))])]),
          day?h('p',day.date+' 相对纯债当日变化 '+money(day.gap)+' 元，累计 '+money(day.cumulativeGap)+' 元。'):h('p','起始收盘尚未产生本区间盈亏。'),
          day?table(['当日分项','贡献（元）'],Object.entries(day.components).map(([k,v])=>[r.mathLabels[k],money(v)])):null,
          day?this.etfTable(day.etfDifference):null,
          day?h('p','前一收盘 ADX '+day.executionDecision.gate.metrics.adx.toFixed(2)+'，+DI '+day.executionDecision.gate.metrics.plusDI.toFixed(2)+'，−DI '+day.executionDecision.gate.metrics.minusDI.toFixed(2)+'；基础 '+day.executionDecision.votes+'/3 票，新增条件'+(day.executionDecision.gate.passed?'满足':'未满足')+'。是否成交还取决于目标切换及执行限制。'):null,
          day?table(['账户','收盘持仓','当日开盘订单'],models.map(m=>[r.models[m],
            '沪深300 '+day.accounts[m].holdings['510300']+'份；国债 '+day.accounts[m].holdings['511010']+'份',
            day.accounts[m].orders.length?day.accounts[m].orders.map(o=>h('p',o.signal+'信号 → '+o.symbol+(o.side==='buy'?'买':'卖')+o.filled+'/'+o.requested+'份，佣金'+money(o.fee)+'元')):'无订单'])):null,
          h('a',{href:this.detailUrl},'Agent · 本区间曲线、逐日分解和订单 JSON')
        ]));
      }
      return nodes;
    }
  }).mount('#adx-bond-app');
})();
