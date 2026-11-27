# 独立前瞻证据包与离线恢复

北京时间 2026 年 11 月 27 日 21:10:38，从 Ubuntu 独立研究库导出首份证据包。包含 10 条采集回执、两次政策审核、1 条样本外评估回执，以及 11 个完整内容归档。以每条回执实际核验或封存时间为边界，保留同一交易日的多次尝试、官方失败响应和手工补采。归档对象按 SHA256 去重。[包内索引](pack/index.json) · [包内哈希清单](pack/manifest.json)

在新目录恢复台账后，离线复算出 1 个应采日、1 个归档日、0 个合格日，首个合格归档为空。再次恢复 20:45 评估所用的原版本记录及代码，按原评估时点重算；结果为等待观察起点。两次政策审核复核出 11 个已审版本和 1 个独立候选事件，政策回测正式入样另有截止和覆盖门槛。

## 从仓库验证和恢复

在当前项目的 Ubuntu 工作目录运行。下面命令只在新目录恢复独立研究台账。

```bash
export PYTHONPATH=src
pack=reports/2026-11-27-portable-observation/pack
scratch=$(mktemp -d)
python scripts/pack_observation_evidence.py verify --pack "$pack"
python scripts/pack_observation_evidence.py restore-ledger \
  --pack "$pack" --destination "$scratch/ledger"
python scripts/pack_observation_evidence.py restore --pack "$pack" \
  --receipt reports/research-evaluation/2026-11-27/50942c432a3e424ba41cc7719cb95583/receipt.json \
  --destination "$scratch/evaluation"
python scripts/seal_observation_evaluation.py \
  --observation-root "$scratch/evaluation" --archive-store "$pack/archive" \
  --verify "$scratch/evaluation/reports/research-evaluation/2026-11-27/50942c432a3e424ba41cc7719cb95583"
python -m unittest discover -s tests -p test_pack_observation_evidence.py -v
```

整份恢复用于重建台账和日历。单条恢复同时取回该归档绑定的原版代码和回执。两种恢复均要求新目录。正式研究后期，跨批次复算还需前批证据和已独立入库的账户、行情等引用对象。此批按当时已有的生产回执验收，盘前决策、开盘取证、标签、模型、预测和月结当时尚无相应的正式归档。运行中、尚未封存的响应仍在生产临时取证目录，待取得正式回执再纳入导出。

后续从生产副本使用 `export --root ... --store ... --output ... --as-of ...` 捕获固定时点。可传 `--after` 做增量，边界为左开右闭，原批次需一并保留。包内只接受独立研究目录、指定公开来源和已绑定的代码与配置。每次发布前执行离线校验。本次证据包由人工触发导出，生产采集与评估继续使用现有定时器。
