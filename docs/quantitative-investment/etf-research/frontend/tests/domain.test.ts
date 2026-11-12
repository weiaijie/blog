import test from 'node:test';
import assert from 'node:assert/strict';
import {defaultPlan,parsePlan,allocationParams,replayParams,comparisonParams,agentManifest,apiUrl} from '../src/domain.ts';
test('saved and shared plans round trip without changing research values',()=>{
 const p=parsePlan({...defaultPlan,capital:'10000.25',portfolios:['3,1,0,6','0,0,0,1','1,0,0,1']});
 assert.deepEqual(parsePlan(JSON.parse(new URLSearchParams({plan:JSON.stringify(p)}).get('plan')!)),p);
 assert.deepEqual(allocationParams(p,true),{start:p.start,end:p.end,capital:'10000.25',fees:'base',weights:'3,1,0,6|0,0,0,1|1,0,0,1',rebalance:'hold'});
});
test('factor replay uses explicit frozen domestic constraints, not the draft weights',()=>{
 const p=parsePlan({...defaultPlan,model:'multifactor_adx_v1',rebalance:'monthly',portfolios:['1,1,1,3']});
 const q=replayParams(p,'1');assert.equal(q.weights,'1,0,0,1');assert.equal(q.rebalance,'signal');assert.equal(q.step,'1');assert.ok(!('installments' in q));
 assert.equal(p.portfolios[0],'1,1,1,3');assert.equal(comparisonParams(p,'technical').capital,p.capital);
 assert.equal(agentManifest(p).requests.replay,apiUrl('/api/v1/backtest/replay',q));
});
test('batches are sent only for installment models and method comparison',()=>{
 const p=parsePlan({...defaultPlan,model:'installments',installments:'5'});
 assert.equal(replayParams(p,'all').installments,'5');assert.equal(replayParams(p,'all').weights,p.portfolios[0]);
 assert.ok(!('installments' in comparisonParams(p,'weights')));assert.equal(comparisonParams(p,'methods').installments,'5');
});
test('invalid imports fail before mutating a plan',()=>{
 for(const change of [{version:2},{extra:'hidden'},{model:'__proto__'},{start:'2021-02-29'},{end:'2018-01-01'},{capital:'Infinity'},{capital:'-1'},{fees:'zero'},{portfolios:['0,0,0,0']},{portfolios:['1,2,3']},{portfolios:['1e2,0,0,1']},{portfolios:['1,0,0,1','1,0,0,1','1,0,0,1','1,0,0,1']},{installments:'13'}])assert.throws(()=>parsePlan({...defaultPlan,...change}));
});
test('single portfolio does not advertise a two-portfolio comparison request',()=>{
 const m=agentManifest(parsePlan({...defaultPlan,portfolios:['0,0,0,1']}));assert.ok(!('compare' in m.requests));assert.ok(m.requests.windows.includes('weights=0%2C0%2C0%2C1'));
});
