# 首次例行样本外评估

北京时间 2026 年 11 月 27 日 20:45:00，独立 Ubuntu 按定时器执行首次样本外评估。报告于 20:45:00.874521 计算，20:45:00.982512 完成归档核验。归档标识为 `dd8d234fc694bdc5e00ee20aa6b0c45ea46df75b650dbb381b94e986413d2c05`。 [评估原始回执](../research-evaluation/2026-11-27/50942c432a3e424ba41cc7719cb95583/receipt.json) · [定时与恢复取证](timer-evidence.json)

运行时核对了 10 条封存采集回执，均未达到独立研究的日期准入条件。正式观察期等待首个合格归档日，评估结果为 `observation_origin_pending`。产出保留 120 个配对交易日、两个样本外季度及含政策组 20 个独立事件的门槛，待实际样本积累后比较。 [报告内容](../research-evaluation/2026-11-27/50942c432a3e424ba41cc7719cb95583/records/evaluation.json)

已按原评估时点在生产证据库重算，逐字段核对报告，并把 20 个绑定文件从内容归档恢复到新目录复验。桌面与手机的「样本外评估」链接都指向相同归档。 [看板](http://10.1.1.120:18766/workbench/#/policy) · [固定归档接口](http://10.1.1.120:18766/api/v1/research/observation/evaluation?archive=dd8d234fc694bdc5e00ee20aa6b0c45ea46df75b650dbb381b94e986413d2c05)

在项目目录验证保存的内容归档及回执。

```bash
PYTHONPATH=src python scripts/seal_observation_evaluation.py \
  --verify reports/research-evaluation/2026-11-27/50942c432a3e424ba41cc7719cb95583 \
  --observation-root . --archive-store reports/2026-11-27-first-live-evaluation/archive-proof
```

原 18 个前瞻账户的收益和净年化证据由各自的账户记录继续积累。独立研究的下一个运行检查是 11 月 28 日 08:25 的补采，以及 11 月 30 日的盘前决策与开盘窗口。
