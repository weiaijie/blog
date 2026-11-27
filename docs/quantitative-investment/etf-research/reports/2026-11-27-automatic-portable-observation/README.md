# 独立研究增量证据首次自动封存

2026 年 11 月 27 日北京时间 22:20:00，Ubuntu 的定时任务首次执行增量导出，于 22:20:02 封存首批。系统日志调用编号和批次回执一致，任务退出码为 0。任务仍启用，下一次为 11 月 28 日 22:20。 [实际运行回执](runtime.json) · [批次回执](batch-receipt.json)

本批接续 11 月 27 日 21:10:38 的基础包，增加 1 条采集回执和 1 个内容归档，即 22:05 的人工来源复查。本次自动封存保留该采集回执的原始类型与实际时间。独立研究合格日仍为 0。 [自动证据包索引](pack/index.json) · [22:05 来源核查](../2026-11-27-after-filing/README.md)

在新目录从基础与本批两个包合并恢复，11 月 27 日 19:55 和 22:05 复查后的单日覆盖、归档和每条来源响应均可精确复算。目录中的 GitHub 证据使用定时任务实际输出。后续每日自动生成可发布批次，GitHub 提交仍按验证与读回流程执行。 [定时规则](../2026-11-27-observation-export/README.md)

在项目目录执行以下命令核验归档对象并恢复链路。

```bash
export PYTHONPATH=src
scratch=$(mktemp -d)
python scripts/pack_observation_evidence.py verify --pack reports/2026-11-27-automatic-portable-observation/pack
python scripts/pack_observation_evidence.py merge --pack reports/2026-11-27-portable-observation/pack --pack reports/2026-11-27-automatic-portable-observation/pack --output "$scratch/merged"
python scripts/pack_observation_evidence.py restore-ledger --pack "$scratch/merged" --destination "$scratch/ledger"
```
