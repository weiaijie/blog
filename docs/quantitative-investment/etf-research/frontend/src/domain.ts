export const symbols=['510300','513500','159920','511010'] as const;
export const names:Record<string,string>={'510300':'沪深300','513500':'标普500','159920':'恒生指数','511010':'国债'};
export const models:Record<string,string>={allocation:'固定配比',installments:'按月分批',trend_120:'120日趋势',multifactor_v1:'三因子投票',multifactor_volume_v1:'三因子＋量价',multifactor_kdj_v1:'三因子＋KDJ',multifactor_adx_v1:'三因子＋ADX'};
export type Params=Record<string,string>;
export type Decimal=string|number;
export interface Plan {version:1;name:string;start:string;end:string;capital:string;fees:string;rebalance:string;model:string;installments:string;portfolios:string[]}
export const defaultPlan:Plan={version:1,name:'沪深300与国债研究',start:'2019-03-20',end:'2026-10-30',capital:'100000',fees:'base',rebalance:'hold',model:'allocation',installments:'3',portfolios:['1,0,0,1','0,0,0,1']};
export function parsePlan(input:unknown):Plan {
  if(!input||typeof input!=='object'||Array.isArray(input)) throw Error('方案须为JSON对象。');
  const d=input as Record<string,unknown>;
  if(Object.keys(d).some(k=>!Object.hasOwn(defaultPlan,k))||Object.keys(defaultPlan).some(k=>!Object.hasOwn(d,k)))throw Error('方案字段不完整，或含未知字段。');
  if(d.version!==1)throw Error('不支持的方案版本。');
  for(const k of ['name','start','end','capital','fees','rebalance','model','installments'])if(typeof d[k]!=='string')throw Error('方案字段类型不正确：'+k);
  const p=d as unknown as Plan;
  if(!p.name.trim()||p.name.length>80)throw Error('方案名须为1至80个字符。');
  for(const x of [p.start,p.end])if(!/^\d{4}-\d{2}-\d{2}$/.test(x)||!Number.isFinite(Date.parse(x))||new Date(x).toISOString().slice(0,10)!==x)throw Error('日期无效。');
  if(p.start>=p.end)throw Error('结束日期须晚于开始日期。');
  if(!/^\d+(\.\d{1,2})?$/.test(p.capital)||+p.capital<1||+p.capital>1e9)throw Error('本金须为1至10亿元，最多两位小数。');
  if(!['low','base','high'].includes(p.fees)||!['hold','monthly'].includes(p.rebalance)||!Object.hasOwn(models,p.model))throw Error('费用、调仓或模型无效。');
  if(!/^(?:[2-9]|1[0-2])$/.test(p.installments))throw Error('分批期数须为2至12。');
  if(!Array.isArray(p.portfolios)||p.portfolios.length<1||p.portfolios.length>3)throw Error('须设置1至3套组合。');
  for(const w of p.portfolios){
    if(typeof w!=='string'||w.split(',').length!==4||w.split(',').some(n=>!/^\d+(\.\d{1,2})?$/.test(n)||+n>99999.99)||w.split(',').reduce((a,b)=>a+Number(b),0)<=0)throw Error('每套组合须含4个非负配比，最多两位小数，合计大于0。');
  }
  return {...p,portfolios:[...p.portfolios]};
}
export function common(p:Plan):Params{return {start:p.start,end:p.end,capital:p.capital,fees:p.fees};}
export function allocationParams(p:Plan,compare=false):Params{return {...common(p),weights:compare?p.portfolios.join('|'):p.portfolios[0]!,rebalance:p.rebalance};}
export function replayParams(p:Plan,step:string):Params{
  const factor=p.model.startsWith('multifactor_'),fixed=factor||p.model==='trend_120';
  return {...allocationParams(p),weights:fixed?'1,0,0,1':p.portfolios[0]!,rebalance:factor?'signal':p.model==='trend_120'?'monthly':p.rebalance,model:p.model,step,...(p.model==='installments'?{installments:p.installments}:{})};
}
export function comparisonParams(p:Plan,kind:string):Params{
  if(kind==='weights')return allocationParams(p,true);
  if(kind==='technical')return common(p);
  return {...common(p),installments:p.installments,rebalance:p.rebalance};
}
export function apiUrl(path:string,params:Params={}):string {const q=new URLSearchParams(params).toString();return path+(q?'?'+q:'');}
export function agentManifest(p:Plan){
  p=parsePlan(p);
  return {schemaVersion:1,plan:p,method:'GET',requests:{
    replay:apiUrl('/api/v1/backtest/replay',replayParams(p,'1')),
    replayAll:apiUrl('/api/v1/backtest/replay',replayParams(p,'all')),
    allocation:apiUrl('/api/v1/backtest',allocationParams(p)),
    windows:apiUrl('/api/v1/backtest/windows',allocationParams(p)),
    ...(p.portfolios.length>1?{compare:apiUrl('/api/v1/backtest/compare',comparisonParams(p,'weights'))}:{}),
    methods:apiUrl('/api/v1/backtest/method-windows',comparisonParams(p,'methods')),
    technical:apiUrl('/api/v1/backtest/technical-factors',comparisonParams(p,'technical')),
  },scope:'allocation/windows/compare use configured weights; methods/technical use fixed domestic models. Replay uses the selected model; trend/factor weights and rebalance are fixed. API validates admitted coverage; a request is not a guarantee of valid coverage.'};
}
export const money=(x:Decimal|null|undefined)=>x==null?'—':Number(x).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2});
export const pct=(x:Decimal|null|undefined)=>x==null?'—':(100*Number(x)).toFixed(2)+'%';
export interface Point{date:string;equity:Decimal;drawdown:Decimal;nav?:Decimal}
export interface Order{signal:string;symbol:string;side:string;requested:number;filled:number;target:number;price:Decimal|null;fee:Decimal;reason:string}
export interface Factor{key:string;label:string;passed:boolean;rule:string;value:Decimal;unit?:string}
export interface Decision{asOf:string;votes:number;regime:string;transition:string;factors:Factor[];gate?:{passed:boolean}}
export interface Signal{signal:string;execution:string;reason:string;target:Record<string,number>;change:Record<string,number>;votes?:number;batch?:number;installments?:number}
export interface Frame extends Point {bars:Record<string,{open:Decimal;high:Decimal;low:Decimal;close:Decimal}>;holdings:Record<string,number>;availableCash:Decimal;receivables:Decimal;dayPnl:Decimal;pnl:Decimal;orders:Order[];nextPlan:Signal|null;decision?:Decision}
export interface Replay{model:string;parameters:Params;step:number;totalSessions:number;frames:Frame[]}
export interface Summary{start:string;end:string;pnl:Decimal;ending_equity:Decimal;total_return:Decimal;annualized_return:Decimal;max_drawdown:Decimal;peak:string;trough:string;recovery:string|null;sessions:number}
export interface Backtest{parameters:Params;summary:Summary;daily:Point[];orders:unknown[]}
export interface Period{count:number;profitable:number;reached:number;worstPnl:Decimal|null;worstReturn?:Decimal|null;worstStart:string|null;worstEnd:string|null}
export interface Windows{parameters:Params;periods:Record<string,Period>}
export interface CompareResult{parameters:Params;portfolios?:Array<Windows&{id:string}>;periods?:Record<string,Record<string,Period>>;overlays?:Record<string,Record<string,Params>>}
export interface Parts{price:Decimal;dividend:Decimal;commission:Decimal;slippage:Decimal;net:Decimal}
export interface Attribution{byEtf:Record<string,Parts>;totals:Parts;accountChange?:Decimal}
export interface GapDay extends Attribution{date:string;change:Decimal;cumulative:Decimal;targetChange:Decimal;referenceChange:Decimal}
export interface Gap{days:GapDay[];increases:string[];decreases:string[]}
export interface IntervalAttribution{start:string;end:string;accounts:Record<string,Attribution>;differences:Record<string,Attribution>}
export interface Overlay{parameters:Params;portfolios:Array<{id:string;summary:Summary;daily:Point[]}>;attribution:{holding:IntervalAttribution;peakToTrough:Record<string,IntervalAttribution>;dailyGaps:Record<string,Gap>}}
export interface ModelDetail{parameters:Params;models:Record<string,{pnl:Decimal;curve:Point[];events:unknown[]}>}
export interface Market{asOf:string;start:string;sessions:number;initial:number;curve:[string,number][];candles:Record<string,[string,number,number,number,number][]>;coverage:Record<string,{quoteStart:string;quoteThrough:string;quotes:number;backtestWindows:string[][]}>}
export interface Options{last:string;domesticFirst:string;overseasFirst:string;trendFirst:string;first:string;preSplitLast:string;splitDay:string}
