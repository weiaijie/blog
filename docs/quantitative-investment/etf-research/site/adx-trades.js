(() => {
  const {createApp,h,nextTick}=Vue, ADX='multifactor_adx_v1';
  const money=x=>Number(x).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  const table=(head,rows)=>h('div',{class:'factor-table'},h('table',[
    h('thead',h('tr',head.map(s=>h('th',{scope:'col'},s)))),
    h('tbody',rows.map(r=>h('tr',r.map((s,i)=>h(i?'td':'th',i?{'data-label':head[i]}:{scope:'row'},s)))))
  ]));
  createApp({
    data:()=>({params:null,report:null,detail:null,busy:false,status:'',request:null,fee:'base',horizon:'2',anchor:0,filter:'all',day:'',url:'',detailUrl:'',title:''}),
    async mounted(){try{const r=await fetch('api/v1/backtest/options');if(!r.ok)throw Error('参数不可用');this.params=(await r.json()).adxTradesDefaults;await this.calculate();}catch(e){this.status=e.message;}},
    beforeUnmount(){this.request?.abort();this.destroy();},
    methods:{
      destroy(){for(const c of this.charts||[])c.remove();this.charts=[];},
      clearDetail(){this.request?.abort();this.request=null;this.busy=false;this.detail=null;this.destroy();this.status='';},
      clear(){this.clearDetail();this.report=null;},
      async query(path,params,controller){
        const url='api/v1/backtest/'+path+'?'+new URLSearchParams(params),r=await fetch(url,{signal:controller.signal}),data=await r.json();
        if(!r.ok)throw Error(data.error||'数据核验失败');return {data,url};
      },
      async calculate(){
        this.clear();const c=new AbortController();this.request=c;this.busy=true;this.status='正在核对四档费用和相同信号；自定义区间可能需要几分钟…';
        try{const r=await this.query('adx-trades',{...this.params},c);if(this.request!==c)return;this.report=r.data;this.url=r.url;this.anchor=0;this.status='';}
        catch(e){if(this.request===c&&e.name!=='AbortError')this.status=e.message;}
        finally{if(this.request===c){this.busy=false;this.request=null;}}
      },
      async open(row,episode=false){
        this.clearDetail();const c=new AbortController();this.request=c;this.busy=true;this.status='正在按原账户重放并逐日对账…';
        const params=episode?{...this.report.parameters,fees:this.fee,episode:row.id}:{...this.report.parameters,start:row.start,end:row.end,fees:this.fee};
        this.title=episode?row.entry+' → '+(row.exit||row.through+'（尚未清仓）'):row.start+' → '+row.end;
        try{
          const r=await this.query('adx-trade-detail',params,c);if(this.request!==c)return;
          const expected=episode?row.pairedGap:row.scenarios[this.fee].gap;
          if(Math.abs(Number(r.data.attribution.differences[ADX+'-bonds'].accountChange)-Number(expected))>1e-6)throw Error('重放与归档差额不一致');
          this.detail=r.data;this.detailUrl=r.url;this.day=r.data.daily.decreases[0]||r.data.daily.days.at(-1).date;this.status='';
          await nextTick();this.paint();document.getElementById('trade-drill').scrollIntoView({block:'start'});
        }catch(e){if(this.request===c&&e.name!=='AbortError')this.status=e.message;}
        finally{if(this.request===c){this.busy=false;this.request=null;}}
      },
      paint(){
        this.destroy();
        for(const [id,key] of [['trade-nav','nav'],['trade-dd','drawdown'],['trade-gap','cumulative']]){
          const chart=LightweightCharts.createChart(document.getElementById(id),{autoSize:true,height:220,layout:{background:{color:'#fff'},textColor:'#40574f'}});
          if(key==='cumulative'){
            const s=chart.addSeries(LightweightCharts.LineSeries,{color:'#9a6b30',title:'ADX − 纯债累计差额（元）'});
            s.setData(this.detail.daily.days.map(r=>({time:r.date,value:Number(r.cumulative)})));
          }else Object.entries(this.detail.curves).forEach(([m,rows],i)=>{
            const s=chart.addSeries(LightweightCharts.LineSeries,{color:i?'#42786a':'#705a91',title:this.report.models[m],lineWidth:2,
              priceFormat:key==='drawdown'?{type:'percent'}:{type:'price',precision:4,minMove:.0001}});
            s.setData(rows.map(r=>({time:r.date,value:Number(r[key])*(key==='drawdown'?100:1)})));
          });
          chart.timeScale().fitContent();chart.subscribeClick(p=>{if(typeof p.time==='string')this.day=p.time;});this.charts.push(chart);
        }
      },
      costTable(scenarios){return table(['费用','净差额：ADX−纯债','加回额外直接成本','按实际成交量加回成本后的差额','零成本重跑差额','数量/资本/执行路径影响'],
        Object.entries(scenarios).map(([f,r])=>[this.report.fees[f],...['gap','extraCosts','fixedFillGrossGap','zeroReplayGap','pathEffect'].map(k=>money(r[k]))]));},
      factors(decision){return decision?table(['因子','当时读数','门槛','通过'],decision.factors.map(f=>[f.label,
        f.metrics?'ADX '+Number(f.value).toFixed(2)+'；+DI '+Number(f.metrics.plusDI).toFixed(2)+'；−DI '+Number(f.metrics.minusDI).toFixed(2):(100*Number(f.value)).toFixed(2)+'%',
        f.rule,f.passed?'是':'否'])):h('p','本日没有前一日执行信号。');}
    },
    render(){
      const nodes=[h('h3','交易体检：哪些买卖值得做？'),h('p','保持 ADX 原规则不变。先查每轮股票持仓，再查费用是否吃掉收益。零成本是诊断假设；原账户和前瞻模型不改变。')];
      if(this.params)nodes.push(h('form',{onSubmit:e=>{e.preventDefault();this.calculate();}},[
        h('div',{class:'work-fields'},[['start','开始日期','date'],['end','结束日期','date'],['capital','每户本金（元）','number']].map(([k,label,type])=>h('label',[label,h('input',{type,required:true,value:this.params[k],
          ...(type==='date'?{min:'2019-03-20',max:'2026-10-30'}:{min:1,max:1e9,step:'.01'}),onInput:e=>{this.params[k]=e.target.value;this.clear();}})]))),
        h('button',{type:'submit',disabled:this.busy},'同时运行低 / 基准 / 高费用及零成本诊断')]));
      nodes.push(h('p',{role:'status'},this.status));if(!this.report)return nodes;
      const r=this.report,book=r.full[this.fee],groups=r.periods[this.horizon],chain=r.nonOverlapping[this.horizon][this.anchor];
      nodes.push(h('h4','同一信号，费用改变了多少结果'),this.costTable(r.fullCosts),
        h('p','加回成本只做原成交量的账面诊断；零成本重跑还会改变整手数量、现金约束和后续资本。额外直接成本＋路径影响＝零成本重跑差额−实际净差额。所有差额单位为元。'),
        h('label',['持有期',h('select',{id:'trade-horizon',value:this.horizon,onChange:e=>{this.horizon=e.target.value;this.anchor=0;}},[h('option',{value:'1'},'1 年'),h('option',{value:'2'},'2 年')])]),
        table(['费用','账户','满期次数','赚钱次数','年化 ≥ 4%','最差盈亏'],Object.entries(groups).flatMap(([f,s])=>Object.entries(s.accounts).map(([m,a])=>[r.fees[f],r.models[m],String(a.count),String(a.profitable),String(a.reached),a.count?money(a.worstPnl):'未满期']))),
        table(['费用','胜纯债','落后纯债','加回额外成本后转正','加回后仍落后','加回后持平'],Object.entries(groups).map(([f,s])=>[r.fees[f],s.beatBonds,s.lagBonds,s.costsReverse,s.grossAlreadyBehind,s.grossTied].map(String))),
        h('p','后三列拆分“落后纯债”的窗口。它们解释账面差额，不证明某笔交易的因果效果；相邻起点高度重叠。'),
        h('label',['下面查看哪档费用',h('select',{id:'trade-fee',value:this.fee,onChange:e=>{this.fee=e.target.value;this.clearDetail();}},Object.entries(r.fees).map(([value,label])=>h('option',{value},label)))]),
        groups[this.fee].worstGap?h('button',{type:'button',disabled:this.busy,onClick:()=>this.open(groups[this.fee].worstGap)},'查看相对纯债最差的满期窗口'):null,
        h('details',[h('summary','不重叠区间：12个预设锚点全部保留'),
          h('p','各链内部收益日不重叠；不同链相互重叠，不能合并成功率。每期从相同现金重新开始，未满期尾段不计。'),
          table(['锚点','满期数','低费用胜纯债','基准胜纯债','高费用胜纯债','零成本胜纯债'],r.nonOverlapping[this.horizon].map(c=>[c.anchor,String(c.windows.length),...Object.keys(r.fees).map(f=>String(c.summaries[f].beatBonds))])),
          h('label',['展开锚点',h('select',{id:'trade-anchor',value:this.anchor,onChange:e=>this.anchor=Number(e.target.value)},r.nonOverlapping[this.horizon].map((c,i)=>h('option',{value:i},c.anchor)))]),
          table(['开始','结束','本档费用净差额','查看'],chain.windows.map(w=>[w.start,w.end,money(w.scenarios[this.fee].gap),h('button',{type:'button',disabled:this.busy,onClick:()=>this.open(w)},'回放')])),
          h('p',chain.immatureTail?'未满期：'+chain.immatureTail.start+' → '+chain.immatureTail.end:'没有未满期尾段')]),
        h('h4','每轮实际股票持仓'),h('p',book.closedCount+' 轮已结束，'+book.openCount+' 轮未清仓；清仓后5个交易日内重新入场 '+book.quickReentries+' 次。持有天数按正股票持仓收盘数计算。'),
        table(['已结束轮次的持有天数','轮数','股票腿净盈亏','股票佣金','股票滑点','股票腿盈利轮数'],book.holdingBands.map(b=>[b.label,String(b.count),money(b.stockNet),money(b.commission),money(b.slippage),String(b.positiveStock)])),
        h('p','这是事后按持有时长分组，不代表预先知道该持有多久。股票腿盈亏与整户相对纯债差额是不同口径，不相加。'),
        h('label',['轮次筛选',h('select',{id:'trade-filter',value:this.filter,onChange:e=>this.filter=e.target.value},[['all','全部，按买入日期'],['worst','股票腿亏损最大优先'],['short','已结束且持有不超过5日'],['open','尚未结束']].map(([value,label])=>h('option',{value},label)))]));
      let episodes=[...book.episodes];if(this.filter==='worst')episodes.sort((a,b)=>Number(a.net)-Number(b.net));
      if(this.filter==='short')episodes=episodes.filter(e=>e.closed&&e.holdingSessions<=5);if(this.filter==='open')episodes=episodes.filter(e=>!e.closed);
      nodes.push(table(['买入','卖出 / 期末','持有交易日','股票毛盈亏','股票费用及滑点','股票净盈亏','同期整户相对纯债','查看'],episodes.map(e=>[e.entry,e.exit||e.through+' 未清仓',String(e.holdingSessions),money(e.gross),money(Number(e.commission)+Number(e.slippage)),money(e.net),money(e.pairedGap),h('button',{type:'button',disabled:this.busy,onClick:()=>this.open(e,true)},'逐日体检')])));
      nodes.push(h('p','轮次期间整户差额 '+money(book.episodeGap)+' ＋ 其余交易日期间差额 '+money(book.outsideEpisodeGap)+' ＝ 全期相对纯债 '+money(book.fullGap)+' 元。各轮沿用原账户资本，没有重新免费建仓。'),h('p',h('a',{href:this.url,target:'_blank',rel:'noopener'},'Agent：共同参数与完整诊断 JSON')));
      if(!this.detail)return nodes;
      const d=this.detail,day=d.daily.days.find(x=>x.date===this.day),ep=d.episode;
      const detail=[h('h4',this.title),h('p',ep?'本轮保留原账户持仓与资本；曲线从买入前一收盘归一化，不是各投入相同新本金。':'该满期窗口从相同现金重新建仓。')];
      if(ep)detail.push(table(['股票腿分项','金额（元）'],[['原价价差',money(ep.price)],['已确认分红',money(ep.dividend)],['其中卖出后除息',money(ep.dividendAfterExit)],['佣金',money(-Number(ep.commission))],['滑点',money(-Number(ep.slippage))],['股票腿净额',money(ep.net)],['期末后尚未除息权益（未计收益）',money(ep.pendingDividend)]]),h('details',[h('summary','入场与退出的前一收盘信号'),h('h5','入场信号'),this.factors(ep.entryDecision),h('h5','退出信号'),this.factors(ep.exitDecision)]));
      detail.push(h('h5','净值走势'),h('div',{id:'trade-nav'}),h('h5','区间收盘回撤'),h('div',{id:'trade-dd'}),h('h5','累计相对纯债盈亏差额'),h('div',{id:'trade-gap'}),
        h('p','点图或选择日期查看：差距拉大最多 '+(d.daily.increases.join('、')||'无')+'；缩小最多 '+(d.daily.decreases.join('、')||'无')+'。'),
        h('label',['核对交易日',h('select',{id:'trade-day',value:this.day,onChange:e=>this.day=e.target.value},d.daily.days.map(x=>h('option',{value:x.date},x.date)))]));
      if(day){
        detail.push(h('p','当日相对纯债 '+money(day.change)+' 元，累计 '+money(day.cumulative)+' 元。'),table(['ETF贡献差','价格','分红','佣金','滑点'],['510300','511010'].map(s=>[s,...['price','dividend','commission','slippage'].map(k=>money(day.byEtf[s][k]))])),
          h('h5','前一收盘信号（用于本日执行）'),this.factors(day.executionDecision));
        for(const [m,a] of Object.entries(day.accounts))detail.push(h('h5',r.models[m]+' · 股票 '+a.holdings['510300']+' 份 / 国债 '+a.holdings['511010']+' 份'),
          a.orders.length?table(['ETF','方向','请求份额','成交份额','原因','佣金'],a.orders.map(o=>[o.symbol,o.side==='buy'?'买入':'卖出',String(o.requested),String(o.filled),o.reason,money(o.fee)])):h('p','本日没有模拟订单。'));
      }
      detail.push(h('a',{href:this.detailUrl,target:'_blank',rel:'noopener'},'Agent：当前区间逐日明细 JSON'));
      nodes.push(h('section',{id:'trade-drill'},detail));return nodes;
    }
  }).mount('#adx-trades-app');
})();
