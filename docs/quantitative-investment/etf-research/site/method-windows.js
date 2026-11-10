(() => {
  const {createApp,h} = Vue;
  const names = {allocation:'一次建仓',installments:'按月分批',trend_120:'120日趋势',multifactor_v1:'多因子 v1'};
  const models = Object.keys(names);
  const money = x => Number(x).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
  const pct = x => (Number(x)*100).toFixed(2)+'%';
  const reasons = {initial:'首次建仓',monthly:'月初调回目标配比',trend_on:'指数高于120日均线，股债各半',trend_off:'指数未高于120日均线，目标全债',
    factor_balanced:'多因子目标：股债各半',factor_bonds:'多因子目标：全债'};
  const fills = {filled:'成交',cash_limited:'现金受限',cash_limited_partial_or_zero:'现金受限',known_ex_dividend_day:'除息保护',opening_halt:'开盘停牌',conservative_9pct_buffer:'价格保护'};
  const symbols = {'510300':'沪深300','511010':'国债'};
  function eventCell(event) {
    if (!event) return '无调仓信号';
    const plan = event.plan;
    const why = plan.reason==='installment' ? '建仓第 '+plan.batch+'/'+plan.installments+' 批' : reasons[plan.reason];
    const items = [h('strong',why),h('small',plan.signal+' 收盘产生信号')];
    if (event.decision) {
      const d=event.decision;
      const votes=event.previousVotes==null?'首次投票 '+d.votes:'票数 '+event.previousVotes+' → '+d.votes;
      items.push(h('p',votes+' / 3，至少两票持有股票。'));
      for (const f of d.factors) {
        const changed=event.changedFactors.includes(f.key);
        const vote=f.passed?'满足':'未满足';
        items.push(h(changed?'strong':'small',(changed?'本日转为':'')+vote+' · '+f.label+' '+(100*Number(f.value)).toFixed(3)+(f.key==='relative60'?' 个百分点':'%')));
      }
    }
    if (plan.trendSpread!=null) items.push(h('small','指数减均线 '+Number(plan.trendSpread).toFixed(5)+'（窗口首日为1）'));
    if (!event.orders.length) items.push(h('p','持仓已达整手目标。'));
    for (const o of event.orders) items.push(h('p',symbols[o.symbol]+(o.side==='buy'?' 买入':' 卖出')+'，计划 '+o.requested+' 份，成交 '+o.filled+' 份'+
      (o.filled?'，模拟价 '+Number(o.price).toFixed(3)+' 元，佣金 '+money(o.fee)+' 元':'')+'（'+fills[o.reason]+'）'));
    return items;
  }
  const cell=(label,content)=>h('td',{'data-label':label},content);
  function table(head, rows, cls='') {
    return h('div',{class:'method-scroll',tabindex:0},[h('table',{class:cls},[
      h('thead',h('tr',head.map(s=>h('th',{scope:'col'},s)))),h('tbody',rows)])]);
  }
  createApp({
    data:()=>({params:null,caseParams:null,caseOpen:false,bounds:[],report:null,detail:null,status:'',busy:false,selected:'',summaryUrl:'',detailUrl:'',generation:0}),
    async mounted() {
      try {
        const res=await fetch('api/v1/backtest/options');
        if (!res.ok) throw Error('接口暂时不可用');
        const opt=await res.json();
        this.params={...opt.methodWindowsDefaults};
        this.caseParams=opt.methodGapCase;
        this.syncHash=()=>{if(location.hash==='#method-gap-case') this.caseOpen=true;};
        this.syncHash();window.addEventListener('hashchange',this.syncHash);
        this.bounds=[this.params.start,this.params.end];
        await this.calculate();
      } catch(e) {this.status=e.message;}
    },
    beforeUnmount() {window.removeEventListener('hashchange',this.syncHash);},
    methods:{
      clear() {this.generation++;this.report=this.detail=null;this.selected=this.status='';this.busy=false;},
      async query(path,params) {
        const url='api/v1/backtest/'+path+'?'+new URLSearchParams(params);
        const res=await fetch(url), data=await res.json();
        if (!res.ok) throw Error(data.error||'回测服务暂时不可用');
        return {data,url};
      },
      async calculate() {
        this.clear();const token=this.generation;this.busy=true;this.status='正在逐个起点核算，自定义参数可能需要几分钟…';
        try {
          const result=await this.query('method-windows',this.params);
          if (token!==this.generation) return;
          this.report=result.data;this.summaryUrl=result.url;this.status='';
        } catch(e) {if(token===this.generation)this.status=e.message;}
        finally {if(token===this.generation)this.busy=false;}
      },
      async worst(model,y) {
        const token=++this.generation, stats=this.report.periods[y][model];
        this.detail=null;this.busy=true;this.selected=names[model]+' · '+y+' 年';this.status='正在重放同一区间的四个账户…';
        try {
          const result=await this.query('method-detail',{...this.report.parameters,start:stats.worstStart,end:stats.worstEnd});
          if (token!==this.generation) return;
          if (Math.abs(Number(result.data.models[model].pnl)-stats.worstPnl)>0.000001) throw Error('最差期金额未对上，请复核。');
          this.detail=result.data;this.detailUrl=result.url;this.status='';
          await this.$nextTick();document.getElementById('method-drill').scrollIntoView({block:'start'});
        } catch(e) {if(token===this.generation)this.status=e.message;}
        finally {if(token===this.generation)this.busy=false;}
      }
    },
    render() {
      const nodes=[h('p','沪深300与国债。每个起点四户各从现金建仓。一次建仓和按月分批目标股债各半；120日趋势每月判断，多因子每日收盘投票。')];
      if (this.params) {
        const field=(key,label,attrs,options)=>{
          const props={name:key,value:this.params[key],...attrs,onChange:e=>{this.params[key]=e.target.value;this.clear();}};
          return h('label',[label,options?h('select',props,options.map(([value,text])=>h('option',{value},text))):h('input',{...props,required:true,onInput:props.onChange})]);
        };
        const dates={type:'date',min:this.bounds[0],max:this.bounds[1]};
        nodes.push(h('form',{onSubmit:e=>{e.preventDefault();this.calculate();}},[
          h('div',{class:'work-fields'},[
            field('start','共同开始日期',dates),field('end','共同结束日期',dates),
            field('capital','每户本金（元）',{type:'number',min:1,max:1e9,step:'.01'}),
            field('fees','共同费用',{},[['low','低费用'],['base','基准费用'],['high','高费用']]),
            field('installments','分批期数',{type:'number',min:2,max:12,step:1}),
            field('rebalance','前两种方式建仓后',{},[['hold','持有到期'],['monthly','每月调回各半']])]),
          h('button',{disabled:this.busy,type:'submit'},'逐日起点 · 并排比较')]));
      }
      nodes.push(h('p',{role:'status'},this.status));
      if (this.caseParams) nodes.push(h('section',{id:'method-gap-case'},[
        h('button',{type:'button','aria-expanded':this.caseOpen,onClick:()=>{this.caseOpen=!this.caseOpen;}},
          (this.caseOpen?'收起':'打开')+' 2021-10-29 至 2022-10-31 三批建仓对账'),
        this.caseOpen?h('p','国债 ETF 贡献了 753.13 元差额。第三批按前一收盘计算，国债预算约 50,359.80 元，400 份需要 50,591.60 元。按每手 100 份取整，分批最终持有 300 份，一次建仓持有 400 份。'):null,
        this.caseOpen?h(window.MethodGap,{params:this.caseParams}):null
      ]));
      if (!this.report) return nodes;
      for (const y of [1,2]) {
        const stats=this.report.periods[y];
        nodes.push(h('h4','持有 '+y+' 年'),table(['投资方式','满期次数','赚钱次数','年化 ≥ 4% 次数','最差到期盈亏','交易对照'],models.map(m=>{
          const s=stats[m];
          return h('tr',[h('th',{scope:'row'},names[m]),cell('满期次数',String(s.count)),cell('赚钱次数',String(s.profitable)),cell('年化 ≥ 4% 次数',String(s.reached)),
            cell('最差到期盈亏',s.count?[money(s.worstPnl)+' 元',h('small',pct(s.worstReturn))]:'—'),
            cell('交易对照',s.count?[h('button',{type:'button',disabled:this.busy,onClick:()=>this.worst(m,y)},'看最差一期'),h('small',s.worstStart+' 至 '+s.worstEnd)]:'无满期窗口')]);
        })));
      }
      nodes.push(h('p',{class:'muted'},'周年遇休市顺延至下个交易日。赚钱按到期盈亏大于零计算；相邻窗口共享行情。最差按到期盈亏排序，并列时取最早一期。'),h('a',{href:this.summaryUrl},'Agent · 本次统计 JSON'));
      if (this.detail) {
        const d=this.detail, entries={};
        for (const m of models) for (const ev of d.models[m].events) (entries[ev.day]??={})[m]=ev;
        nodes.push(h('section',{id:'method-drill'},[h('h4',this.selected+'最差一期 · 同区间买卖对照'),
          h('p',d.start+' 至 '+d.end+'，四户各从 '+money(d.parameters.capital)+' 元起步。'),
          h('p','多因子每天检查沪深300是否高于120日均线、近60日是否跑赢国债、20日年化波动是否低于25%。粗体标出较上一收盘改变的一票。'),
          h('a',{href:'backtest.html?'+new URLSearchParams({model:'multifactor_v1',start:d.start,end:d.end,weights:'1,0,0,1',capital:d.parameters.capital,fees:d.parameters.fees})+'#replay'},'逐日回放本期多因子账户'),
          table(['开盘执行日',...models.map(m=>names[m])],[
            h('tr',[h('th','到期盈亏'),...models.map(m=>cell(names[m],money(d.models[m].pnl)+' 元'))]),
            ...Object.keys(entries).sort().map(day=>h('tr',[h('th',{scope:'row'},day),...models.map(m=>cell(names[m],eventCell(entries[day][m])))]))],'method-log'),
          h(window.MethodGap,{key:this.detailUrl,params:d.parameters}),
          h('a',{href:this.detailUrl},'Agent · 同期逐日净值、信号和订单 JSON')]));
      }
      return nodes;
    }
  }).mount('#method-app');
})();
