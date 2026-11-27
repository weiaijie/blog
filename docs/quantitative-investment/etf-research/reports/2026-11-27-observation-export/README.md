# 独立研究增量证据定时导出

用户级 systemd 定时任务每天北京时间 22:20 封存增量证据。时间安排在每日评估与月度覆盖检查之后。主机恢复后补跑时使用实际启动时点。定时器触发身份及真实时间落入回执。导出范围是上一次已验证水位之后、本次启动时点及之前取得的独立研究回执。

- 固定以仓库保存的首份独立证据包为起点，在 Ubuntu 逐字节核验其 SHA256。增量包记录上一份包的清单校验值和当前水位。
- 中断或校验失败将保留开始记录与暂存证据。成功后才原子发布批次。下次按最后成功水位继续。重复调用标记可防止同一次定时调用追加两批。
- 生产包与运行台账使用分开位置，留存供后续发布和复现。GitHub 发布仍按每批验证、提交和读回执行。
- 读取批次状态会核对时间边界、清单绑定和最后一批的对象。恢复整个序列时用 `pack_observation_evidence.py merge` 对每批对象逐项复验。
- 这项工作只封存既有证据。正式采集、资金与政策样本准入依原规则运行。

[基础证据包](../2026-11-27-portable-observation/README.md) · [增量包恢复示例](../2026-11-27-after-filing/README.md)

```bash
systemctl --user list-timers etf-research-observation-export.timer
journalctl --user -u etf-research-observation-export.service -n 10 --no-pager
```

自动导出的首次生产执行及 GitHub 读回另存运行回执。隔离验收使用真实已封存的独立研究证据，核验导出边界、重跑、断点恢复与清单冲突。
