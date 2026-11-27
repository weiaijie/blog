"""Reproduce the independent study closeout from the published evidence chain."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from audit_observation_repository import CATALOG, audit
from forward_milestones import publication_report
from observation_evaluation_status import ARCHIVE_ID, latest_evaluation
from observation_out_of_sample import VARIANT_NAMES, evaluate, midterm_review
from run_research_observation import first_archive
from etf_research.observation_experiment import MIN_EVENTS, MIN_QUARTERS, MIN_TEST
from etf_research.policy_events import instant
from etf_research.publication import create, inside, read, sha

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = dict(policy='量价＋政策',etf='量价＋份额净值',margin='量价＋两融',combined='量价＋全部')
OUTCOMES = dict(insufficient_samples='样本不足',improved='有样本外改善证据',not_established='未证实改善',
                uncertain='区间估计不足',exploratory='分组探索结果')
ACCOUNT_STATES = dict(accumulating='积累中',calendar_unverified='日历待核验',awaiting_valuation='等待到期估值',
                      awaiting_publication='等待正式发布',publication_unverified='发布证据待核验',
                      ledger_conflict='账本待对齐',complete='已核验')


def from_evidence(project, root, store, published, *, archive=None):
    cutoff = instant(published['publishedThrough'])
    result = dict(schemaVersion=1,publishedThrough=cutoff.isoformat(),
                  publishedManifestSha256=published['publishedManifestSha256'])
    origin = first_archive(root,store,cutoff)
    if origin is None:
        return dict(result,status='observation_origin_pending')
    selected,issues = latest_evaluation(root,store,cutoff,archive=archive)
    if selected is None or issues['unverified']:
        return dict(result,status='evaluation_evidence_unverified' if issues['unverified'] else 'awaiting_evaluation',
                    archiveIssues=issues)
    receipt,report = selected
    if report['studyOrigin'] is None:
        return dict(result,status='awaiting_evaluation',evaluationArchiveSha256=receipt['archiveSha256'])
    if report['studyOrigin'] != origin:
        raise ValueError('Evaluation belongs to a different published observation origin')
    if report['status'] != 'evaluation_available':
        return dict(result,status=report['status'],evaluationArchiveSha256=receipt['archiveSha256'])

    if set(report['comparisons']) != set(VARIANT_NAMES):
        raise ValueError('Closeout evaluation is missing a registered comparison')
    if any(group['economics'].get('status')=='economic_evidence_unverified'
           for group in report['comparisons'].values()):
        return dict(result,status='economic_evidence_unverified',evaluationArchiveSha256=receipt['archiveSha256'])
    if any(group['score']['status'] not in OUTCOMES for group in report['comparisons'].values()):
        raise ValueError('Closeout evaluation is missing a registered outcome')

    binding = read(inside(root,receipt['path'])/'records/evaluation.json')
    protocol_hash = sha(project/'PROTOCOL_OBSERVATION_V1.md')
    if binding['codeSha256']['PROTOCOL_OBSERVATION_V1.md'] != protocol_hash:
        raise ValueError('Research protocol differs from the sealed evaluation')
    observed = instant(report['asOf'])
    replay = evaluate(root,store,observed)
    if 'midtermReview' in report:
        replay['midtermReview'] = midterm_review(root,store,replay)
    if replay != report:
        raise ValueError('The published evaluation does not reproduce at its original cutoff')
    forward = publication_report(project,observed)
    return dict(result,status='ready',evaluationReceipt=receipt,evaluation=report,
                protocolSha256=protocol_hash,forward=forward)


def percent(value):
    return '待核验' if value is None else f'{float(value):.2%}'


def render(result):
    report = result['evaluation']
    lines = ['# ETF 独立前瞻研究 12 个月结题报告','',
             f"正式观察起点 {report['studyOrigin']['date']}，结题周年 {report['finalOn']}。"
             f"本报告按 {report['asOf']} 的封存评估复算。",'',
             f"评估归档 SHA256 `{result['evaluationReceipt']['archiveSha256']}`。"
             f"公开证据链末端清单 SHA256 `{result['publishedManifestSha256']}`。",'',
             f'正式比较每组至少需要 {MIN_TEST} 个成对日期、{MIN_QUARTERS} 个样本外季度，含政策组另需 {MIN_EVENTS} 个独立事件。','',
             '| 比较 | 成对日期 | 样本外季度 | 独立政策事件 | 结果 |','| --- | ---: | ---: | ---: | --- |']
    for name,group in report['comparisons'].items():
        row = group['score']
        events = row['independentEvents'] if name in ('policy','combined') else '—'
        lines.append(f"| {VARIANTS[name]} | {row['completedPairs']} | {row['quarters']} | {events} | {OUTCOMES[row['status']]} |")

    main = report['comparisons']['combined']
    score = main['score']
    lines.extend(['','## 主要比较',''])
    if 'baselineMae' in score:
        for index,label in enumerate(('五日净收益','五日最大回撤')):
            base,expanded=percent(score['baselineMae'][index]),percent(score['expandedMae'][index])
            interval=score['pairedImprovementInterval']
            limits='区间待核验' if interval is None else '至'.join(f'{100*value:.3f} 个百分点' for value in interval[index])
            lines.append(f'- {label}平均绝对误差为 {base} 和 {expanded}，配对改善区间为 {limits}。')
    else:
        shortfall = main['shortfall']
        lines.append(f"含全部数据的主比较还差 {shortfall['pairs']} 个日期、{shortfall['folds']} 个季度和 "
                     f"{shortfall['policyEvents']} 个独立政策事件。")
    costs = main['economics']
    lines.extend(['','## 非重叠窗口经济对照','',
                  f"按预登记日历选了 {costs['selectedWindows']} 个窗口，其中 {costs['matchedWindows']} 个可同日核对。"])
    if costs.get('averages'):
        lines.extend(['','| 基准费用情景 | 平均五日净收益 | 平均最大回撤 | 平均佣金 | 平均滑点 | 有未成交窗口 |',
                      '| --- | ---: | ---: | ---: | ---: | ---: |'])
        names=dict(fixed_50_50='固定 50/50',bond_only='只持国债',baseline='量价基线配置',expanded='全数据配置')
        for key,scenarios in costs['averages'].items():
            row=scenarios['base']
            lines.append(f"| {names[key]} | {percent(row['terminalReturn'])} | {percent(row['maxDrawdown'])} | "
                         f"{float(row['commission']):.2f} 元 | {float(row['slippage']):.2f} 元 | "
                         f"{row['windowsWithUnfilledOrders']} |")
    lines.extend(['','## 原 18 户模拟账户',''])
    forward=result['forward']
    if forward is None:
        lines.append('公开仓库在结题时点的账户发布证据待核验。')
    else:
        base=forward['progress']['monthly_50_50_base']
        lines.append(f"可核验账户数据至 {forward['asOf']}，共 {forward['returnIntervals']} 个收益区间。"
                     f"基准费用月度 50/50 组合累计净收益 {percent(base['netReturn'])}，"
                     f"最大收盘回撤 {percent(base['maxCloseDrawdown'])}。")
        for step in forward['milestones']:
            if step['months']>=12:
                stats=step['accounts']
                value = stats['monthly_50_50_base'] if stats else None
                state = ACCOUNT_STATES[step['state']]
                note = f"，基准费用月度 50/50 净年化 {percent(value['netAnnualized'])}" if value else ''
                lines.append(f"- {step['months']} 个月复盘日 {step['anniversary']}，{state}{note}。")
    lines.extend(['','[完整评估、逐日排除原因、各费用情景和 18 户原口径](result.json)',''])
    return '\n'.join(lines)


def run(project, destination, *, archive=None):
    with TemporaryDirectory(prefix='etf-closeout-') as temp:
        evidence = Path(temp)/'evidence'
        provenance = audit(project,read(project/CATALOG),destination=evidence)
        result=from_evidence(project,evidence/'ledger',evidence/'pack/archive',provenance,archive=archive)
    if result['status']!='ready':
        return result
    document=render(result)
    destination.mkdir(parents=True,exist_ok=False)
    create(destination/'result.json',result)
    with (destination/'README.md').open('x',encoding='utf-8',newline='\n') as output:
        output.write(document)
    return dict(status='ready',evaluationArchiveSha256=result['evaluationReceipt']['archiveSha256'],
                publishedThrough=result['publishedThrough'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path,help='New directory for the reproducible closeout')
    parser.add_argument('--archive',help='Reproduce a published evaluation by its archive SHA256')
    args=parser.parse_args()
    if args.archive is not None and not ARCHIVE_ID.fullmatch(args.archive):
        parser.error('Expected a 64-character evaluation SHA256')
    print(json.dumps(run(ROOT,args.output,archive=args.archive),ensure_ascii=False,allow_nan=False))


if __name__ == '__main__':
    main()
