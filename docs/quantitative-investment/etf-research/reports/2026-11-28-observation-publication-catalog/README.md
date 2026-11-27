# 独立研究公开归档核验与恢复

[公开目录](../research-observation-publication/catalog.json)登记基础包、定时增量的原始回执和当前链尾。复现命令依次核对目录的 SHA256、每一批的前份清单与时间边界、回执计数和实际归档对象。Ubuntu 的生产批次与 GitHub 中的各批原始回执逐字节核对。生产已封存而 GitHub 尚未收录的批次会按原批次号列出。

在 GitHub 检出的 ETF 项目目录中，用 Ubuntu Python 环境运行下列命令。恢复位置应是新目录。恢复结果包含合并后的 `pack/archive` 与同批的 `ledger`，可直接按原时点运行覆盖和评估命令。

```bash
PYTHONPATH=src python scripts/audit_observation_repository.py --restore-to ./recovered-observation
```

在 Ubuntu 上核对生产发布进度时，传入服务使用的生产导出目录。

```bash
PYTHONPATH=src python scripts/audit_observation_repository.py --live-spool "$HOME/projects/etf-research-observation-exports"
```

## 首次读回

以 11 月 27 日 22:20 的自动增量为链尾，核对 GitHub 已保存的基础包和真实首批，与 Ubuntu 的生产导出链一致。恢复 12 个归档中的 683 个台账文件，保留 11 条采集、2 条政策审核和 1 条评估回执。按同一截止时点重算 11 月 27 日，恢复目录和生产台账的单日响应逐字段相同。当时的 10 次采集尝试结论仍是部分齐备。 [核验结果](verification.json) · [首次定时导出](../2026-11-27-automatic-portable-observation/README.md)

下一批发布时，将原始回执及证据包加入 GitHub，在目录尾部追加对应的路径和回执哈希，再推进链尾。先对比生产目录，提交后从 GitHub 读回并运行核验。两次核验都读取真实归档水位，采集准入仍由各交易日的独立证据决定。现有夜间任务负责封存批次，公开目录随已验证的 GitHub 发布推进。

回归覆盖链尾批次缺失、原回执变动、前批清单被替换，以及生产有下一批而公开目录尚未收录。
