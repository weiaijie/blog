(() => {
  const {h} = Vue;
  const url = 'api/v1/backtest/factor-shortfall';
  const money = v => Number(v).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  window.FactorShortfall = {
    props:{eventCell:{type:Function,required:true}},
    data:()=>({report:null,row:null,events:[],detailUrl:'',error:'',busy:false}),
    async mounted() {
      this.controller=new AbortController();
      try {
        const res=await fetch(url,{signal:this.controller.signal});
        if (!res.ok) throw Error('归因报告暂时不可用');
        this.report=await res.json();
        await this.select(this.report.largestAbsolute[0]);
      } catch(e) {if (e.name!=='AbortError') this.error=e.message;}
    },
    beforeUnmount() {this.controller.abort();},
    methods:{
      async select(start) {
        this.controller.abort();
        const controller=new AbortController();
        this.controller=controller;
        const row=this.report.windows.find(r=>r.start===start);
        this.row=row;this.events=[];this.error='';this.busy=true;this.detailUrl='';
        const query=new URLSearchParams({...this.report.parameters,start,end:row.end});
        const path='api/v1/backtest/method-detail?'+query;
        try {
          const res=await fetch(path,{signal:controller.signal});
          if (!res.ok) throw Error('本期交易记录暂时不可用');
          const data=await res.json(), factor=data.models.multifactor_v1;
          if (Math.abs(Number(factor.pnl)-Number(data.models.allocation.pnl)-Number(row.gap))>.000001)
            throw Error('成交回放与归档差额不符');
          if (controller.signal.aborted) return;
          this.events=factor.events;this.detailUrl=path;
        } catch(e) {if (!controller.signal.aborted) this.error=e.message;}
        finally {if (!controller.signal.aborted) this.busy=false;}
      },
      trade(event) {return h('li',{key:event.day},[h('p',event.day+' 开盘执行'),...this.eventCell(event)]);}
    },
    render() {
      if (!this.report) return h('p',{role:'status'},this.error||'正在读取窗口归因…');
      const c=this.report.counts, r=this.row, ep=r.worstEpisode;
      const switches=this.events.filter(e=>ep && (e.day===ep.entry || e.day===ep.exit));
      return h('div',{class:'shortfall-report'},[
        h('p','10万元本金，基准费用。'+c.windows+' 个两年窗口盈利且年化低于 4%，其中 '+c.behind+' 期跑输同日起点的一次建仓，'+c.allocationReached+' 期的一次建仓达到 4%。'),
        h('p',c.missedRally+' 期实际退出股票后，错过上涨且股债合计拖累收益。全部窗口中 '+c.extraCost+' 期比一次建仓多付交易成本。'),
        h('p','保持实际成交份额和首次建仓成本，只加回后续换仓佣金与滑点，'+c.switchAddbackReached+' 期可达到年化 4%。其中 '+this.report.windows.filter(w=>w.switchAddbackReached&&w.missedRally).length+' 期也存在退出股票后的净拖累。'),
        h('p','保留信号、免佣金和滑点，有 '+c.noCostReached+' 期达到 4%。首次股债各半指令后持有、仍收基准费用，有 '+c.retainReached+' 期达到；其中 '+c.bothReached+' 期在两种回放中都达到。'),
        h('div',{class:'method-gap-ranks'},[h('strong','期末绝对差额最大'),...this.report.largestAbsolute.map(start=>{
          const w=this.report.windows.find(w=>w.start===start);
          return h('button',{type:'button','aria-pressed':start===r.start,onClick:()=>this.select(start)},start+' · '+money(w.gap)+' 元');
        })]),
        h('label',['查看其他起点 ',h('select',{value:r.start,onChange:e=>this.select(e.target.value)},
          this.report.windows.map(w=>h('option',{value:w.start},w.start+' 至 '+w.end+'　'+money(w.gap)+' 元')))]),
        h('h4',r.start+' 至 '+r.end+' · 多因子减一次建仓'),
        h('p','收盘权益：多因子 '+money(r.factorEquity)+' 元，一次建仓 '+money(r.allocationEquity)+' 元，相差 '+money(r.gap)+' 元。'),
        h('table',[h('thead',h('tr',[h('th','差额来源'),h('th','对期末差额的贡献（元）')])),
          h('tbody',[
            ['退出股票后的沪深300（含分红）',r.exitStock],['同期国债（含分红）',r.exitBond],
            ['首笔即全债期间',r.initialBonds],['其余持仓期间',r.otherExposure],
            ['佣金差',Number(r.allocationCommission)-Number(r.factorCommission)],
            ['滑点差',Number(r.allocationSlippage)-Number(r.factorSlippage)],['合计',r.gap]
          ].map(([title,v])=>h('tr',[h('th',{scope:'row'},title),h('td',{'data-label':'贡献（元）'},money(v))])))]),
        h('p','本期首次建仓后的换仓佣金 '+money(r.switchCommission)+' 元、滑点 '+money(r.switchSlippage)+' 元。按原份额加回后'+(r.switchAddbackReached?'达到':'仍低于')+'年化 4%。'),
        h('p','本期达标所需权益 '+money(r.threshold)+' 元；零佣金、零滑点回放 '+money(r.noCostEquity)+' 元；首次股债各半指令后持有 '+money(r.retainEquity)+' 元。'),
        ep?h('p','退出股票 '+r.exits+' 次。相对表现最差的一段从 '+ep.entry+' 开盘起，至 '+(ep.exit?ep.exit+' 开盘买回':'期末收盘')+'，股债持仓合计贡献 '+money(ep.net)+' 元。'):h('p','本期没有从持有股票转为全债。'),
        this.error?h('p',{role:'alert'},this.error):null,
        this.busy?h('p',{role:'status'},'正在核对同期信号和成交…'):null,
        switches.length?h('ol',switches.map(this.trade)):null,
        this.events.length?h('details',[h('summary','本期全部 '+this.events.length+' 次收盘计划和次日执行'),h('ol',this.events.map(this.trade))]):null,
        h('a',{href:url},'Agent · 全部窗口归因 JSON'),this.detailUrl?h('a',{href:this.detailUrl},'　Agent · 本期翻票和成交 JSON'):null
      ]);
    }
  };
})();
