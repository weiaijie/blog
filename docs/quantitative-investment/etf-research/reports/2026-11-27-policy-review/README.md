# 首批政策审核与截止时点核验

截至北京时间 2026-11-27 18:00，独立管线累计 **0 个合格归档交易日**。这次验收处理候选原文和真实可用时间。

## 公告审核

11 月 27 日 17:20 左右采集的 10 个候选修订已逐条核对。审核结果于 17:54:55 封存，绑定采集归档、公告正文哈希、判定及正文定位。

| 判定 | 文章数 | 内容 |
| --- | ---: | --- |
| 同一政策事件 | 2 | 中国政府网与证监会刊载同一次国务院常务会议部署。归为 `state-council-2026-11-27-stabilization`，阶段为部署。两篇正文均未给出可据此确认的生效日。 |
| 监测期前资料 | 7 | 日期早于注册起点，保留候选原文和判断依据。 |
| 研究范围外 | 1 | 证监会处罚案例回顾，保留范围判定及原文。 |

[逐条判定](decisions.json) · [真实审核回执](../research-policy-reviews/2026-11-27-capture-092054/receipt.json) · [原始采集批次](../research-observation/runs/2026-11-27/20261127T092054Z-465a8da5)

## 决策截止与缺口

11 月 30 日 08:55 决策的[真实回算](coverage-probe.json)在 11 月 27 日 18:00 读取当时证据。政策窗口共 5 个截止间隔、14 个预定采集时点。回算时有 8 个已到时点缺合格记录，另有 6 个时点尚未到。政策覆盖为 **0/5**，已观察到 1 个通过审核的独立事件，`policyActiveCount` 留空。7 个量价基线仍可复算，本次为管线验收。

政策覆盖限于中国政府网和证监会的已登记栏目。每个预定时点要有两来源归档，候选各版本必须在所属区间截止前完成审核，空候选批次也须明确核对。重复正文在哈希及候选标识一致时沿用先前审核。临时补抓、错过采集时点、迟到审核和新修订都保留各自时间。独立定时采集会持续刷新最近完成交易日，即使该日已经合格。

## 离线复验

在项目目录使用锁定的 Python 环境执行。

```bash
PYTHONPATH=src python scripts/review_policy_observations.py \
  --verify reports/research-policy-reviews/2026-11-27-capture-092054 \
  --observation-root . --archive-store reports/2026-11-27-observation-inputs/archive-proofs
PYTHONPATH=src python scripts/observation_inputs.py \
  --verify reports/2026-11-27-policy-review/coverage-probe.json \
  --archive-store reports/2026-11-27-observation-inputs/archive-proofs
```

下一里程碑是接通 08:55 前正式封存、核验例行采集的连续性与首次合格归档，同时保留迟到和来源缺口。12 个月结题时间从首个独立生产合格归档日计算。
