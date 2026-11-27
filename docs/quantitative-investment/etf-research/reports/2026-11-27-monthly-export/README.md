# 月度覆盖接入夜间导出与恢复

月度覆盖在独立服务内封存，实际回执目录为 reports/research-monthly-coverage。夜间导出原来扫描另一目录，可能在未收录月结时仍成功推进导出水位。现已对齐真实目录，并允许月结归档携带已绑定 SHA256 的采集回执。之后可以单独恢复月报及其所绑定的回执，也可以把月结增量与前续包合并，恢复完整覆盖台账并按原时点复算。 [导出器](../../scripts/pack_observation_evidence.py) · [定时配置](../../deploy/etf-research-observation-export.timer)

本轮在隔离目录从三份已公开证据包恢复 12 条真实采集回执、2 条政策审核和 1 条评估回执。用测试时钟验证 12 月 1 日 08:54:59 月报仍开放，21:05 能封存该隔离场景。22:20 的隔离增量准确收录 1 份月结回执及 1 个内容归档，单独恢复 60 个归档文件。合并后使用原计算时间复算，月报、回执哈希及工作台和 Agent 共用的响应逐字段相同。隔离场景未写入正式台账。 [回归与负例](../../tests/test_observation_monthly.py)

合并生产包时按每批真实起止水位选取连续的包。手工补充包可用于单独查证。后续定时包覆盖相同区间时，使用连续定时序列完成恢复。 [自动导出与恢复](../2026-11-27-observation-export/README.md)

11 月正式月报仍处于等待封存。按已核验日历，最后应采交易日为 11 月 30 日。若 12 月 1 日 08:55 已过且流程正常，21:05 封存，22:20 导出。独立研究当前仍为 1 日归档、0 日合格。 [月度覆盖口径](../2026-11-27-monthly-coverage/README.md)

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_observation_monthly.py -v
```
