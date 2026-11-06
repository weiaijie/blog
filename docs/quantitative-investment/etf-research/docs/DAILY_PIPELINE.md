# 每日管线操作与恢复

仅研究模拟。冻结引擎、协议、策略、此前目标不变。运行入口是scripts/run_daily.py；使用独立Ubuntu和requirements-lock.txt，Python3.12.16已验证。Windows仅承担采集/桌面验证，不使用WSL。

## 一次运行

在项目目录执行：

```bash
python scripts/run_daily.py
```

按北京时间16:00与独立日历选择最近完整交易日。没有新日则验证现有检查点/报告包后返回up_to_date，零网络请求；已有日重建必须显式--rebuild，不增加观察日。存在新日则：

1. flock进程锁；生成唯一reports/daily/时间-随机ID目录，x模式写入，不重用旧目录。
2. collect_update采双源OHLC、官方公告目录，collect_official_close采上交所日线和即时快照；新data/snapshots目录保存请求、原文、错误、时间、SHA256。
3. 原admission严格核验日历、双源、旧价格前缀、公告目录、官方分红；第三源逐日比较及当日收盘快照核对。任何变化/缺失/失败阻断，绝不补造。
4. advance从旧检查点重放并证明旧账本前缀不变；持续核对11月6日冻结目标。独立Decimal逐日重算日志现金、应收、持仓和净值，日线外模型成交单独标明。该核对不是完整独立分红/费用规则引擎，也不是实际成交凭证。
5. 用显式新输入配置生成标准风险、Beta/压力/披露代理页面和当日主页面；历史研究保持原样。
6. 检查期间输入未变化，写ready.json和完整manifest，fsync文件/目录；最后os.replace一次切换config/active_run.json。读者从site/daily.html进入同一个完整报告包。旧报告/检查点不覆盖，失败包不会成为当前状态。

config/research.json保留固定报告的基础配置；管线产生每次独立research.json与risk_extensions_config.json。当前指针列出实际配置，不能混读旧默认输入和新日报。提交后的完整性清单是该Git版本的基线；未来运行产生新文件/切换指针后，应审阅、更新该轮清单并提交，不将未提交新输出冒称已在GitHub保存。

## 重放、准备及恢复

```bash
# 已有合法证据重建当前日（仍然不增加观察日）
python scripts/run_daily.py --rebuild --candidate 2026-11-06-close-windows-1653 --official 2026-11-06-official-close-1650
# 仅准备封存；验证后可以恢复发布
python scripts/run_daily.py --rebuild --candidate 2026-11-06-close-windows-1653 --official 2026-11-06-official-close-1650 --prepare-only
python scripts/run_daily.py --resume reports/daily/实际运行ID
# 部分写入或失败：留住旧目录，新建一次尝试（按需提供新候选证据）
python scripts/run_daily.py --retry-of reports/daily/实际失败ID
```

恢复已发布包返回already_published，不重复计算；已封存未发布包须manifest、输入哈希、旧指针、检查点协议/引擎一致才可切换。若期间代码/配置/来源变了，不能强行恢复，需新运行重做。部分写入没有manifest时拒绝发布，使用新尝试保留旧证据。锁随进程退出释放，不删除锁文件inode。验证的是进程退出与本地文件系统原子性，不宣称覆盖硬件损坏、跨主机分布式事务或全部断电场景。

## Ubuntu定时方案（尚未启用）

deploy/etf-research-daily.service与.timer为用户单位，项目位于/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research，Python环境/home/ubuntu/projects/etf-research-py312。路径必须核实，不覆盖旧环境。设定周一至五16:10 Asia/Shanghai、Persistent=true；即使补运行也需通过日历和截止时间门槛。

已通过systemd-analyze --user verify与calendar；下个计划时间为2026-11-09 16:10北京时间。使用相同工作目录、Python、NoNewPrivileges、PrivateTmp、UMask等属性的systemd用户一次性服务受控运行成功，返回up_to_date。timer未安装/启用，没有后台长期执行证明。Ubuntu公告TLS超时仍阻断真实采集，需先解决并验证；不能禁用TLS校验。暂不安装或启动timer。

部署时将审核后的单位文件链接到用户systemd，核实用户manager及无人登录时linger行为，再执行enable --now；这是后续运行配置，不包含本轮已启用的承诺。日志为本地journal和不可变失败包；不发送邮件/微信，不自动推GitHub，不存凭据。公网托管未验收。

参考：[Python flock文档](https://docs.python.org/3.12/library/fcntl.html#fcntl.flock)；systemd单位语法以Ubuntu本机systemd-analyze实际验证为准。

更新Ubuntu代码时先核对未保存输出：不要用旧归档覆盖config/active_run.json、reports/daily或新快照。先将运行证据同步到Git工作树、审阅提交；源码增量更新后才重试。运行中的代码变更会触发哈希阻断，不能强制恢复旧准备包。
