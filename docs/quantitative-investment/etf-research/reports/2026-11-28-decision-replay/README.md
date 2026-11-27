# 盘前封存输入按原时点复算

`seal_observation_decision.py --reproduce` 先验证回执、封存目录及内容归档，再按记录的决策日、证据截止、计算时间与恢复版本重新装配特征。逐字段比较数值、缺口、原始证据路径、哈希和各组准入状态。若输入未封存、记录口径不可识别或复算不同，命令失败并指出原因。

```bash
PYTHONPATH=src python scripts/seal_observation_decision.py --reproduce "$decision" \
  --observation-root "$ledger" --archive-store "$store" --price-project "$prices"
```

`decision` 是所选封存回执的目录。`ledger`、`store` 和 `prices` 分别是该回执对应的研究台账、内容归档和行情发布仓。按同一版研究代码和那次证据所含的行情版本运行。

## 实际证据

11 月 28 日 02:07，在 Ubuntu 隔离目录用生产归档对 11 月 30 日盘前输入封存试跑并重算，7 个量价输入、510300 和 511010 两项份额净值比率均逐字段复算。融资买入占比及政策计数仍为空。这次是诊断回执，正式前瞻资格仍须等待 systemd 生产采集和决策封存。 [隔离复算](verification.json)

已公开的基础包、22:20 定时增量和 22:23 份额补采包可为更早的截止时点独立重建上述 9 个数值。证据引用和时点仍遵循各自归档。使用[补采包恢复说明](../2026-11-27-cleared-shares/README.md)获得 `$scratch/ledger` 和 `$scratch/merged/archive`，然后在 GitHub 检出的 ETF 项目执行以下命令。

```bash
PYTHONPATH=src python scripts/observation_inputs.py \
  --verify reports/2026-11-28-decision-replay/published-inputs.json \
  --observation-root "$scratch/ledger" --archive-store "$scratch/merged/archive"
```

[公开证据逐字段复算快照](published-inputs.json)保留该时点的来源、计算时间和仍未知的输入。回归验证同一次封存可以按原时点复算，金额或特征值改变后复算拒绝通过。
