function mountStrategyControls(onChange) {
  const {createApp, reactive, h} = Vue;
  const initialModel = new URLSearchParams(location.search).get('model');
  const state = reactive({model:initialModel?.startsWith('multifactor_')?initialModel:'allocation', batches:'3', rebalance:'monthly'});
  function select(label, id, key, choices) {
    return h('label', [label, h('select', {
      id, value:state[key], onChange:event=>{
        state[key]=event.target.value;
        onChange();
      }
    }, choices.map(([value,text])=>h('option',{value},text)))]);
  }
  createApp({render() {
    const staged=state.model==='installments', trend=state.model==='trend_120';
    const multi=state.model.startsWith('multifactor_');
    const gate={multifactor_volume_v1:'此外，量比须大于1且当日含分红收益为正。',multifactor_kdj_v1:'此外，KDJ 的 K 必须高于 D。',multifactor_adx_v1:'此外，ADX 必须至少25且 +DI 高于 −DI。'}[state.model]||'';
    const monthly=state.rebalance==='monthly';
    const fields=[select('投资方式','replay-model','model',[
      ['allocation','一次建仓 · 固定配比'],['installments','按月分批建仓'],['trend_120','按趋势调仓 · 沪深300'],['multifactor_v1','多因子 v1 · 每日两票触发'],['multifactor_volume_v1','三因子＋量价确认 v1'],['multifactor_kdj_v1','三因子＋KDJ v1'],['multifactor_adx_v1','三因子＋ADX v1']])];
    if (staged) fields.push(select('建仓期数','replay-batches','batches',
      Array.from({length:11},(_,i)=>[String(i+2),(i+2)+' 期'])));
    const buy = multi ? '沪深300高于120日均线、60日收益跑赢国债、20日年化波动低于25%，每项各一票。收盘满足至少两项，目标为沪深300与国债各50%。' : trend ? '首次及每月首个开盘前检查。沪深300含分红指数高于120日均线，目标为股债各50%。' :
      staged ? '起始资金分 '+state.batches+' 期。第1期目标投入总资产的 '+(100/Number(state.batches)).toLocaleString('zh-CN',{maximumFractionDigits:1})+'%，此后每月首个开盘提高一个等份，最后一期目标为100%。其余资金留作现金。' :
      '按上方配比，以首日收盘计算份额，在下一交易日开盘模拟建仓。';
    const sell = multi ? '基础票不足两票'+(gate?'或新增条件不满足':'')+'，目标转为全债。首次或目标切换时下单，下一交易日开盘先卖后买；信号持续时持有，未成交部分等待下次切换。' : trend ? '指数等于或低于均线，目标转为全债。按目标差额先卖后买。' :
      staged ? '每批按当期目标补买或减持。满期后'+(monthly?'每月调回配比。':'持有至结束。') :
      monthly ? '每月调回目标配比：超配卖出、低配补买。' : '采用仅初始建仓，之后持有至期末。';
    return h('div',[h('div',{class:'replay-controls'},fields),
      h('dl',{class:'strategy-rules',id:'replay-rule'},[h('dt','买入条件'),h('dd',buy+gate),h('dt','卖出与调仓'),h('dd',sell)])]);
  }}).mount('#strategy-controls');
  return state;
}
