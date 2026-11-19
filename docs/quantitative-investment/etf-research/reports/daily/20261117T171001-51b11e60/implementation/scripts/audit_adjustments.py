"""Offline falsification of a single-factor vendor HFQ model, not a return model."""
from pathlib import Path
from decimal import Decimal as D, ROUND_HALF_UP
import json,argparse,hashlib
parser=argparse.ArgumentParser();parser.add_argument('--snapshots',type=Path,default=Path(__file__).resolve().parents[1]/'data/snapshots');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
p=args.snapshots/'2026-11-02';e=args.snapshots/'2026-11-03-official-02'/'reconciliation.json'
events=json.loads(e.read_text())['dividends'];output={'scope':'Frozen 2026-11-02 data, 640 common completed sessions; no backtest','sources':{},'symbols':{}}
for c in ['510300','511010']:
 sources=[p/f'sina_daily_{c}.body',p/f'tencent_hfq_{c}.body',p/f'tencent_raw_{c}.body',e]
 for f in sources:output['sources'][str(f.relative_to(args.snapshots))]=hashlib.sha256(f.read_bytes()).hexdigest()
 s=sources[0].read_text();raw={r['day']:r for r in json.loads(s[s.index('([')+1:s.rindex(')')])};hfq=json.loads(sources[1].read_text())['data']['sh'+c]['hfqday'];pairs=[]
 for row in hfq:
  cumulative=sum((D(v['per_share']) for v in events if v['symbol']==c and v['ex_date']<=row[0]),D(0))
  for k,i in [('open',1),('close',2),('high',3),('low',4)]:pairs.append((D(raw[row[0]][k])+cumulative,D(row[i])))
 half=D('.0005');lo=max((y-half)/x for x,y in pairs);hi=min((y+half)/x for x,y in pairs)
 factor=D('0.37094933') if c=='510300' else D(1)
 offset_lo=max(y-half-x*factor for x,y in pairs);offset_hi=min(y+half-x*factor for x,y in pairs)
 t=json.loads(sources[2].read_text())['data']['sh'+c]['day'];vol=[(D(raw[r[0]]['volume']),D(r[5])) for r in t if r[0] in raw]
 output['symbols'][c]={'price_fields':len(pairs),'factor_lower_bound':str(lo),'factor_upper_bound':str(hi),'single_factor_feasible':lo<=hi,'official_initial_ratio_used_for_comparison':str(factor),'affine_offset_lower':str(offset_lo),'affine_offset_upper':str(offset_hi),'affine_offset_feasible':offset_lo<=offset_hi,'offset_status':'In-sample diagnostic interval only; not supplier-confirmed and prohibited for strategy inputs','volume_rows':len(vol),'rounded_sina_over_100_matches_tencent':sum((v/100).quantize(D(1),rounding=ROUND_HALF_UP)==t for v,t in vol),'unit_status':'Empirical rounding match only; no primary endpoint unit specification obtained'}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2));print(json.dumps(output['symbols'],ensure_ascii=False,indent=2))
