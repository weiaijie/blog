(() => {
  const {createApp,h,nextTick} = Vue;
  const money=n=>Number(n).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  const pct=n=>(100*Number(n)).toFixed(2)+'%';
  const colors=['#536674','#bd7044','#287762','#705a91'];
  const symbols={'510300':'沪深300','511010':'国债'};
  const fills={filled:'成交',cash_limited:'现金受限',cash_limited_partial_or_zero:'现金受限',known_ex_dividend_day:'除息保护',opening_halt:'开盘停牌',conservative_9pct_buffer:'价格保护'};
  function table(headers,rows) {
    return h('div',{class:'factor-table'},h('table',[
      h('thead',h('tr',headers.map(x=>h('th',{scope:'col'},x)))),
      h('tbody',rows.map(row=>h('tr',row.map((v,i)=>h(i?'td':'th',i?{'data-label':headers[i]}:{scope:'row'},v)))))
    ]));
  }
  createApp({
    data:()=>({params:null,report:null,detail:null,status:'',busy:false,request:null,selected:'',day:'',eventModel:'multifactor_v1',summaryUrl:'',detailUrl:''}),
    async mounted() {
      try {
        const r=await fetch('api/v1/backtest/options');if(!r.ok)throw Error('参数接口暂时不可用');
        this.params=(await r.json()).technicalFactorsDefaults;
        await this.calculate();
      } catch(e){this.status=e.message;}
    },
    beforeUnmount(){this.request?.abort();this.destroyCharts();},
    methods:{
      destroyCharts(){for(const chart of this.charts||[])chart.remove();this.charts=[];},
      clear(){this.request?.abort();this.request=null;this.busy=false;this.report=this.detail=null;this.status='';this.destroyCharts();},
      async query(path,params,controller) {
        const url='api/v1/backtest/'+path+'?'+new URLSearchParams(params);
        const res=await fetch(url,{signal:controller.signal}), data=await res.json();
        if(!res.ok)throw Error(data.error||'研究数据暂时不可用');
        return {data,url};
      },
      async calculate() {
        this.clear();const c=new AbortController();this.request=c;this.busy=true;
        this.status='正在核算四个版本，自定义参数可能需要几分钟…';
        try {
          const {data,url}=await this.query('technical-factors',{...this.params},c);
          if(this.request!==c)return;this.report=data;this.summaryUrl=url;this.status='';
        } catch(e){if(this.request===c && e.name!=='AbortError')this.status=e.message;}
        finally{if(this.request===c){this.busy=false;this.request=null;}}
      },
      async worst(model,years) {
        this.request?.abort();const c=new AbortController();this.request=c;this.busy=true;this.detail=null;this.destroyCharts();
        const stats=this.report.periods[years][model];
        this.status='正在回放同一起点的四个独立账户…';this.selected=this.report.models[model]+' · '+years+' 年最差一期';
        try {
          const params={...this.report.parameters,start:stats.worstStart,end:stats.worstEnd};
          const {data,url}=await this.query('technical-detail',params,c);
          if(this.request!==c)return;
          if(Math.abs(Number(data.models[model].pnl)-stats.worstPnl)>0.000001)throw Error('最差期金额与账户不一致，请复核。');
          this.detail=data;this.detailUrl=url;this.eventModel=model;this.day=data.models[model].events[0]?.date||'';this.status='';
          await nextTick();this.paint();document.getElementById('factor-drill').scrollIntoView({block:'start'});
        } catch(e){if(this.request===c && e.name!=='AbortError')this.status=e.message;}
        finally{if(this.request===c){this.busy=false;this.request=null;}}
      },
      paint() {
        this.destroyCharts();
        for(const [id,key] of [['factor-equity','equity'],['factor-drawdown','drawdown']]) {
          const chart=LightweightCharts.createChart(document.getElementById(id),{autoSize:true,height:240,
            layout:{background:{color:'#fff'},textColor:'#40574f'},rightPriceScale:{borderVisible:false},timeScale:{timeVisible:false}});
          Object.entries(this.detail.models).forEach(([model,value],i)=>{
            const line=chart.addSeries(LightweightCharts.LineSeries,{color:colors[i],lineWidth:2,title:this.report.models[model],
              priceFormat:key==='drawdown'?{type:'percent'}:{type:'price',precision:2,minMove:.01}});
            line.setData(value.curve.map(r=>({time:r.date,value:Number(r[key])*(key==='drawdown'?100:1)})));
          });
          chart.timeScale().fitContent();
          chart.subscribeClick(p=>{if(typeof p.time==='string')this.day=p.time;});
          this.charts.push(chart);
        }
      }
    },
    render() {
      const nodes=[h('h3','成交量、KDJ、ADX · 独立对照'),
        h('p','原三因子至少两票，再分别增加一种确认条件。满足时股债各半，否则全债。参数固定，不按结果调参。'),
        h('p',{class:'muted'},'量价：当日量高于此前20日均量且上涨；KDJ：K > D；ADX：≥25 且 +DI > −DI。新增条件每天生效，目标变化后次日开盘模拟。')];
      if(this.params) {
        const field=(key,label,type)=>h('label',[label,h('input',{type,value:this.params[key],required:true,
          ...(type==='date'?{min:'2019-03-20',max:'2026-10-30'}:{min:1,max:1e9,step:'.01'}),
          onInput:e=>{this.params[key]=e.target.value;this.clear();}})]);
        nodes.push(h('form',{onSubmit:e=>{e.preventDefault();this.calculate();}},[
          h('div',{class:'work-fields'},[field('start','共同开始','date'),field('end','共同结束','date'),field('capital','每户本金（元）','number'),
            h('label',['共同费用',h('select',{value:this.params.fees,onChange:e=>{this.params.fees=e.target.value;this.clear();}},
              [['base','基准费用'],['low','低费用'],['high','高费用']].map(([value,label])=>h('option',{value},label)))])]),
          h('button',{type:'submit',disabled:this.busy},'运行四版本对照')]));
      }
      nodes.push(h('p',{role:'status'},this.status));
      if(!this.report)return nodes;
      const models=Object.keys(this.report.models);
      for(const y of [1,2]) nodes.push(h('h4','持有 '+y+' 年'),table(
        ['版本','满期次数','赚钱 / 亏钱 / 持平','年化 ≥ 4%','比原三因子赚得多','最差到期盈亏','查看'],
        models.map(m=>{const s=this.report.periods[y][m];return [this.report.models[m],String(s.count),s.profitable+' / '+s.losing+' / '+s.flat,
          String(s.reached),m==='multifactor_v1'?'基准':String(s.beatBaseline||0),s.count?money(s.worstPnl)+' 元':'—',
          s.count?h('button',{type:'button',disabled:this.busy,onClick:()=>this.worst(m,y)},'看最差一期'):'无满期窗口'];})));
      nodes.push(h('h4','整个所选区间 · 交易和成本'),table(['版本','到期盈亏','最大收盘回撤','持有股票日数','成交笔数','佣金','滑点'],
        models.map(m=>{const s=this.report.fullPeriod[m];return [this.report.models[m],money(s.pnl),pct(s.maxDrawdown),s.stockHoldingDays+' / '+s.observations,String(s.trades),money(s.commission),money(s.slippage)];})),
        h('p',{class:'muted'},'窗口相互重叠，次数不是未来赚钱概率。成交量已与上交所交叉核验，换手率与实际成交能力仍未知。KDJ 初始化与部分行情软件不同。'),
        h('p','同区间仅持有国债参考：盈亏 '+money(this.report.bondReference.pnl)+' 元，最大回撤 '+pct(this.report.bondReference.maxDrawdown)+'。该参考只展示完整区间，不混入上面的逐日起点计数。'),
        h('a',{href:this.summaryUrl},'Agent · 同参数统计 JSON'));
      if(this.detail) {
        const d=this.detail,book=d.models[this.eventModel],ev=book.events.find(r=>r.date===this.day);
        const params={...d.parameters,weights:'1,0,0,1',model:this.eventModel};
        nodes.push(h('section',{id:'factor-drill'},[
          h('h4',this.selected+' · 四版本同区间'),
          h('p',d.parameters.start+' 至 '+d.parameters.end+'；以下为账户金额及收盘回撤。点图选日期，展开当日信号与成交。'),
          table(['版本','本期盈亏','最大回撤'],models.map((m,i)=>[h('span',{style:{color:colors[i]}},this.report.models[m]),money(d.models[m].pnl),pct(d.models[m].maxDrawdown)])),
          h('div',{id:'factor-equity',class:'factor-chart'}),h('div',{id:'factor-drawdown',class:'factor-chart'}),
          h('div',{class:'work-fields'},[
            h('label',['查看模型',h('select',{value:this.eventModel,onChange:e=>{this.eventModel=e.target.value;this.day=d.models[this.eventModel].events[0]?.date||'';}},
              models.map(m=>h('option',{value:m},this.report.models[m])))]),
            h('label',['信号或成交日',h('select',{value:this.day,onChange:e=>{this.day=e.target.value;}},
              [...(book.events.some(e=>e.date===this.day)?[]:[h('option',{value:this.day},this.day+' · 无新目标或成交')]),...book.events.map(e=>h('option',{value:e.date},e.date))])])]),
          h('p',this.day+' · '+(ev?'当日账户 '+money(ev.equity)+' 元':'当日无新目标或成交；逐日回放可查看持续状态。')),
          ev?h('ul',ev.decision.factors.map(f=>h('li',f.label+'：'+(f.passed?'满足':'未满足')+'；'+f.rule+'；读数 '+(f.unit==='raw'?Number(f.value).toFixed(3):pct(f.value))+
            (f.metrics?'；K '+f.metrics.k.toFixed(2)+' / D '+f.metrics.d.toFixed(2)+' / J '+f.metrics.j.toFixed(2)+'；量比 '+f.metrics.volumeRatio.toFixed(2)+'；ADX '+f.metrics.adx.toFixed(2)+' / +DI '+f.metrics.plusDI.toFixed(2)+' / −DI '+f.metrics.minusDI.toFixed(2)+'；当日收益 '+pct(f.metrics.return):'')))):null,
          ev?h('p','收盘基础 '+ev.decision.votes+' / 3 票'+(ev.decision.gate?'，新增条件'+(ev.decision.gate.passed?'满足':'未满足'):'')+'；目标'+(ev.decision.regime==='balanced'?'股债各半':'全债')+
            (ev.nextPlan?'，计划 '+ev.nextPlan.execution+' 开盘执行。':'，本日不生成新订单。')):null,
          ev?h('p','持仓：'+Object.entries(ev.holdings).map(([s,n])=>symbols[s]+' '+n+' 份').join('，')):null,
          ev?h('ul',ev.orders.map(o=>h('li',o.signal+' 收盘信号 → 本日 '+symbols[o.symbol]+(o.side==='buy'?'买':'卖')+' '+o.filled+'/'+o.requested+' 份，佣金 '+money(o.fee)+' 元；'+(fills[o.reason]||o.reason)))):null,
          h('p',[h('a',{href:'backtest.html?'+new URLSearchParams(params)+'#replay'},'逐日回放当前版本的全部信号和成交'),' · ',h('a',{href:this.detailUrl},'Agent · 四户曲线与信号 JSON')])
        ]));
      }
      return nodes;
    }
  }).mount('#factor-lab-app');
})();
