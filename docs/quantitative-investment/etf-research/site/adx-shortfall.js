(() => {
  const {createApp,h,nextTick}=Vue,ADX='multifactor_adx_v1';
  const money=x=>Number(x).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  const table=(head,rows)=>h('div',{class:'factor-table'},h('table',{class:head.length===2?'adx-parts':''},[
    h('thead',h('tr',head.map(s=>h('th',{scope:'col'},s)))),
    h('tbody',rows.map(r=>h('tr',r.map((s,i)=>h(i?'td':'th',i?{'data-label':head[i]}:{scope:'row'},s)))))
  ]));
  const missedLabels={stockUp:'上涨日股票贡献差（负为少赚）',stockDown:'下跌日股票贡献差（正为少亏）',stockFlat:'平盘日股票贡献差',bond:'同期国债替代贡献差',commission:'同期佣金差',slippage:'同期滑点差'};
  createApp({
    data:()=>({report:null,detail:null,status:'正在读取固定321个窗口…',busy:false,request:null,selected:'',year:'all',day:'',detailUrl:''}),
    async mounted(){try{const r=await fetch('api/v1/backtest/adx-shortfall');const data=await r.json();if(!r.ok)throw Error(data.error);this.report=data;this.selected=data.worstStarts[0];this.status='';}catch(e){this.status=e.message;}},
    beforeUnmount(){this.request?.abort();this.destroy();},
    methods:{
      destroy(){for(const c of this.charts||[])c.remove();this.charts=[];},
      async open(start){
        this.request?.abort();const c=new AbortController();this.request=c;this.busy=true;this.detail=null;this.destroy();this.status='重放原账户与事后诊断，逐项核对差额…';this.selected=start;
        try{
          const url='api/v1/backtest/adx-shortfall-detail?'+new URLSearchParams({start});const r=await fetch(url,{signal:c.signal}),data=await r.json();
          if(!r.ok)throw Error(data.error||'核验失败');if(this.request!==c)return;
          this.detail=data;this.detailUrl=url;this.day=data.replay.daily.decreases[0]||data.replay.daily.days.at(-1).date;this.status='';
          await nextTick();this.paint();document.getElementById('shortfall-drill').scrollIntoView({block:'start'});
        }catch(e){if(this.request===c&&e.name!=='AbortError')this.status=e.message;}
        finally{if(this.request===c){this.busy=false;this.request=null;}}
      },
      jump(day){this.day=day;nextTick(()=>document.getElementById('shortfall-day-detail').scrollIntoView({block:'start'}));},
      paint(){
        this.destroy();const d=this.detail;
        for(const [id,key] of [['shortfall-nav','nav'],['shortfall-dd','drawdown'],['shortfall-gap','gap']]){
          const c=LightweightCharts.createChart(document.getElementById(id),{autoSize:true,height:230,layout:{background:{color:'#fff'},textColor:'#40574f'}});
          if(key==='gap'){
            for(const [field,label,color] of [['cumulative','实际净差额','#705a91'],['cumulativeGrossGap','按原成交量加回额外成本','#b4794c']]){
              const s=c.addSeries(LightweightCharts.LineSeries,{title:label,color,lineWidth:2});s.setData(d.replay.daily.days.map(r=>({time:r.date,value:Number(r[field])})));
            }
          }else{
            for(const [m,rows] of Object.entries(d.replay.curves)){
              const s=c.addSeries(LightweightCharts.LineSeries,{title:d.replay.models[m],color:m===ADX?'#705a91':'#42786a',lineWidth:2,
                priceFormat:key==='drawdown'?{type:'percent'}:{type:'price',precision:4,minMove:.0001}});
              s.setData(rows.map(r=>({time:r.date,value:Number(r[key])*(key==='drawdown'?100:1)})));
            }
          }
          c.timeScale().fitContent();c.subscribeClick(p=>{if(typeof p.time==='string')this.day=p.time;});this.charts.push(c);
        }
      },
      factors(decision){return decision?table(['因子','前收盘读数','规则','通过'],decision.factors.map(f=>[f.label,
        f.metrics?'ADX '+Number(f.value).toFixed(2)+'；+DI '+Number(f.metrics.plusDI).toFixed(2)+'；−DI '+Number(f.metrics.minusDI).toFixed(2):(Number(f.value)*100).toFixed(2)+'%',f.rule,f.passed?'是':'否'])):h('p','起始观察日，没有前一收盘执行信号。');},
      orders(rows){return rows.length?table(['ETF','方向','请求份额','成交份额','模型价格','佣金','模拟状态'],rows.map(o=>[o.symbol,o.side==='buy'?'买入':'卖出',String(o.requested),String(o.filled),Number(o.modeled_price).toFixed(3),money(o.fee),({filled:'已全部模拟成交',cash_limited:'现金约束'}[o.reason]||o.reason)+(o.outside_range?'（模型价超日线范围）':'')])):h('p','本日没有订单。');}
    },
    render(){
      const nodes=[h('h3','加回费用仍落后：321个两年窗口'),h('p','固定原清单、每户10万元、基准费用。买入后的股票损益、卖出后的机会成本、反复换仓诊断采用不同对照，分别核对，不相加。'),h('p',{role:'status'},this.status)];
      if(!this.report)return nodes;
      const r=this.report,n=r.counts;
      nodes.push(table(['核查角度','窗口数量 / 321'],[['股票价差＋分红合计为负',String(n.negativeStock)],['股票合计为正，仍不足弥补国债收益差',String(n.positiveStock)],['卖出后上涨日存在股票少赚（另与股债各半比较）',String(n.missedRise)],['清仓后5个交易日内重买',String(n.shortGapWindows)]]),
        h('p','这些标签会重叠，不是互斥原因。上涨时少赚与下跌时少亏必须一起看；空仓只持国债本身不会产生“相对纯债错过股票上涨”的损失。'),
        h('h4','加回费用后差距最大的五期'),table(['开始','满期','实际净差额','加回费用后差额','股票价差＋分红','查看'],r.worstStarts.map(start=>{const w=r.windows.find(x=>x.start===start);return[w.start,w.end,money(w.netGap),money(w.grossGap),money(w.stockGross),h('button',{type:'button',disabled:this.busy,onClick:()=>this.open(start)},'拆开这一期')];})),
        h('p','以上按加回费用后差额排序。相邻起点共享行情，不能当作五次独立失败。'),
        h('div',{class:'work-actions'},[['missedRise','看上涨日少赚最多的窗口'],['cancellationBest','看取消短空档改善最多的窗口'],['cancellationWorst','看取消短空档改善最小的窗口']].map(([k,label])=>h('button',{type:'button',disabled:this.busy,onClick:()=>this.open(r.diagnosticStarts[k])},label))),
        h('details',[h('summary','全部321个窗口与起点年份'),h('p',Object.entries(r.entryYears).map(([y,c])=>y+'年 '+c+'期').join('；')),
          h('label',['筛选起点年份',h('select',{id:'shortfall-year',value:this.year,onChange:e=>this.year=e.target.value},[h('option',{value:'all'},'全部'),...Object.keys(r.entryYears).map(y=>h('option',{value:y},y))])]),
          table(['起点','满期','加回成本后差额','短空档数','查看'],r.windows.filter(w=>this.year==='all'||w.start.startsWith(this.year)).map(w=>[w.start,w.end,money(w.grossGap),String(w.churn.pairs),h('button',{type:'button',disabled:this.busy,onClick:()=>this.open(w.start)},'查看窗口')]))]),
        h('h4','反复换仓：窗口多不等于独立事件多'),
        table(['实际卖出','实际重买','被多少窗口包含'],r.shortGapEvents.map(e=>[e.exit,e.reentry,String(e.windowCount)])),
        h('p','事后取消这些短空档，价格/分红持仓路径改善 '+n.cancellationGrossBetter+' 期、变差 '+n.cancellationGrossWorse+' 期、不变 '+n.cancellationGrossEqual+' 期；取消后加回额外成本仍落后纯债 '+n.cancellationGrossStillBehind+' 期。实验使用未来才知道的重买日期，不能当作当时可执行的策略。'),
        h('p',h('a',{href:'api/v1/backtest/adx-shortfall',target:'_blank',rel:'noopener'},'Agent：固定样本、口径及全部窗口 JSON')));
      if(!this.detail)return nodes;
      const d=this.detail,w=d.summary,c=w.churn,o=w.opportunity,day=d.replay.daily.days.find(x=>x.date===this.day),cf=d.counterfactual.daily.days.find(x=>x.date===this.day),missed=d.missedDays.find(x=>x.date===this.day);
      const detail=[h('h4',w.start+' → '+w.end),h('h5','一、相对纯债：钱具体亏在哪里'),
        table(['账目分项','金额（元）'],[...Object.entries(d.labels).map(([key,label])=>[label,money(w.components[key])]),['实际净差额合计',money(w.netGap)],['加回额外佣金与滑点后',money(w.grossGap)]]),
        h('p','前四项之和等于加回费用后的差额，全部六项之和等于账户净差额。亏损股票轮次和盈利轮次都保留，期末未清仓按收盘市值计算。'),
        table(['买入','卖出 / 期末','持有收盘数','股票价差','确权分红','股票毛盈亏','查看买卖日'],d.episodes.map(e=>[e.entry,e.exit||e.through+' 未清仓',String(e.holdingSessions),money(e.price),money(e.dividend),money(e.gross),h('span',[h('button',{type:'button',onClick:()=>this.jump(e.entry)},'看买入'),e.exit?h('button',{type:'button',onClick:()=>this.jump(e.exit)},'看卖出'):null])])),
        h('h5','二、卖出后错过上涨，也可能避开下跌'),h('p','以下改与同日起点一次建仓股债各半比较，只算卖出后的完整无股票日，共 '+o.days+' 日；卖出日、重买日及首次买入前空仓不混入。'),
        table(['另一基准下的贡献差','金额（元）'],[...Object.entries(missedLabels).map(([k,label])=>[label,money(o.components[k])]),['上述无股票日合计',money(o.selectedDaysGap)],['其他日期合计',money(o.otherDaysGap)],['全期相对股债各半',money(o.fullBalancedGap)]]),
        h('p','上涨/下跌逐日贡献累计可能很大且互相抵消，不是实际赚到或亏掉这么多钱。这里的金额不与上面的纯债差额相加。'),
        h('h5','三、如果事后取消短空档换仓'),h('p','仅为事后诊断：已知5个交易日内会重买，删除这段卖出和重买目标批次，其他计划不变，重新处理整手、费用和现金。原策略没有被修改。'),
        table(['取消短空档实验','金额（元）'],[['股票/国债价格与分红路径改善',money(c.priceDividendPath)],['佣金和滑点节省',money(c.costsSaved)],['净收益改善（两项之和）',money(c.netImprovement)],['取消后仍相对纯债的净差额',money(c.alternativeNetGap)],['取消后加回额外成本的差额',money(c.alternativeGrossGap)]]),
        table(['实际清仓','实际重买','间隔交易日','取消目标批次','查看'],d.counterfactual.pairs.map(p=>[p.exit,p.reentry,String(p.gapSessions),p.removedTargets.join('、'),h('span',[h('button',{type:'button',onClick:()=>this.jump(p.exit)},'看清仓日'),h('button',{type:'button',onClick:()=>this.jump(p.reentry)},'看重买日')])])),
        h('p',c.pairs?'取消换仓后的改善包含后续持仓和资本变化，不能全部叫作手续费，也不能证明ADX有预测能力。':'本期没有符合定义的短空档，没有删除任何目标，诊断结果应与原账户一致。'),
        h('h5','原账户净值走势'),h('div',{id:'shortfall-nav'}),h('h5','原账户区间回撤'),h('div',{id:'shortfall-dd'}),h('h5','原账户相对纯债：累计净差额与加回成本差额'),h('div',{id:'shortfall-gap'}),
        h('p','差距扩大最多：'+(d.replay.daily.decreases.join('、')||'无')+'；缩小最多：'+(d.replay.daily.increases.join('、')||'无')),
        h('label',['点图或选择日期',h('select',{id:'shortfall-day',value:this.day,onChange:e=>this.day=e.target.value},d.replay.daily.days.map(x=>h('option',{value:x.date},x.date)))])];
      if(day){
        const body=[h('h5',this.day+' · 因子与买卖记录'),h('p','当日净差额 '+money(day.change)+' 元；加回额外成本后 '+money(day.grossChange)+' 元；累计加回后 '+money(day.cumulativeGrossGap)+' 元。'),
          table(['ETF贡献差','价格','分红','佣金','滑点'],['510300','511010'].map(s=>[s,...['price','dividend','commission','slippage'].map(k=>money(day.byEtf[s][k]))])),
          h('p','执行依据是前一收盘。相较更前一日翻票：'+(day.changedFactors.join('、')||'无 / 初始观察')+'。'),this.factors(day.executionDecision),
          h('p',missed?'本日属于上述卖出后完整无股票日，另基准贡献差 '+money(missed.accountGap)+' 元。':'本日不属于上述卖出后完整无股票日。')];
        for(const [m,a] of Object.entries(day.accounts))body.push(h('h5',d.replay.models[m]+'：股票 '+a.holdings['510300']+' 份 / 国债 '+a.holdings['511010']+' 份'),this.orders(a.orders));
        body.push(h('details',[h('summary','本日事后取消换仓诊断的订单（非原策略）'),this.orders(cf?.orders||[]),h('p','本日相对原ADX改善 '+money(cf?.change||0)+' 元，累计 '+money(cf?.cumulative||0)+' 元。')]));
        detail.push(h('div',{id:'shortfall-day-detail'},body));
      }
      detail.push(h('p',h('a',{href:this.detailUrl,target:'_blank',rel:'noopener'},'Agent：本窗口因子、订单、三个视角及逐日对账 JSON')));
      nodes.push(h('section',{id:'shortfall-drill'},detail));return nodes;
    }
  }).mount('#adx-shortfall-app');
})();
