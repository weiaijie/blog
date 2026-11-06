# 每日管线操作与恢复

仅研究模拟。冻结引擎、协议、策略、此前目标不变。日常监督入口是scripts/run_scheduled.py，内部管线是scripts/run_daily.py；使用独立Ubuntu和requirements-lock.txt，Python3.12.16已验证。Windows仅承担采集/桌面验证，不使用WSL。

## 一次运行

在项目目录执行：

```bash
python scripts/run_scheduled.py
```

按北京时间16:00与独立日历选择最近完整交易日。没有新日则验证现有检查点/报告包后返回up_to_date，零网络请求；已有日重建必须显式--rebuild，不增加观察日。存在新日则：

1. flock进程锁；生成唯一reports/daily/时间-随机ID目录，x模式写入，不重用旧目录。
2. collect_update采双源OHLC、官方公告目录，collect_official_close采上交所日线和即时快照。共用成熟curl的IPv4 HTTPS传输，DNS解析域名并正常校验证书；config/collection.json限定8秒连接、25秒全程、最多3次尝试及2/4秒退避。新data/snapshots目录保留每次attempt原文、HTTP/证书状态、错误、时间、SHA256，以及选中响应。证书失败及非暂时性HTTP状态不在同一请求中反复重试，HTTP200也仍须严格语义核验。
3. 原admission严格核验日历、双源、旧价格前缀、公告目录、官方分红；第三源逐日比较及当日收盘快照核对。任何变化/缺失/失败阻断，绝不补造。
4. advance从旧检查点重放并证明旧账本前缀不变；持续核对11月6日冻结目标。独立Decimal逐日重算日志现金、应收、持仓和净值，日线外模型成交单独标明。该核对不是完整独立分红/费用规则引擎，也不是实际成交凭证。
5. 用显式新输入配置生成标准风险、Beta/压力/披露代理页面和当日主页面；历史研究保持原样。
6. 检查期间输入未变化，写ready.json和完整manifest，fsync文件/目录；最后os.replace一次切换config/active_run.json。读者从site/daily.html进入同一个完整报告包。旧报告/检查点不覆盖，失败包不会成为当前状态。

config/research.json保留固定报告的基础配置；管线产生每次独立research.json与risk_extensions_config.json。当前指针列出实际配置，不能混读旧默认输入和新日报。静态完整性清单保护代码、配置、历史证据与报告。三个可变入口config/active_run.json、site/operation_status.json与site/health_status.json由verify_project.py分别对照封存账户包/运行记录验证，不使用过期Git哈希把正常日更新误报为篡改；其他静态文件仍按哈希阻断。新输出须审阅提交后才算已存GitHub。

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

## Ubuntu定时运行（已启用）

用户已于2026-11-06明确授权启用。deploy/etf-research-daily.service与.timer已链接至ubuntu用户systemd并enabled/active；loginctl的Linger=yes。主机是独立ubuntu-server，不使用WSL。工作目录为/home/ubuntu/projects/etf-research-git-snapshot/docs/quantitative-investment/etf-research，解释器为/home/ubuntu/projects/etf-research-py312/bin/python。

- 每周一至五北京时间16:10执行，16:40和17:10作为补尝试；Persistent=true。独立日历排除休市，16:00门槛不变。
- 定时器激活或重载后30秒补检查。账户已是最新则零网络请求；这是运行检查，不是新增前瞻收益。
- 进程失败120秒后重试，20分钟最多3次启动。外部来源错误和公告变化仍阻断发布；重试不代表自动批准。
- 服务限时15分钟，监督器子进程限时780秒，停止宽限30秒，KillMode=control-group，PrivateTmp及NoNewPrivileges开启。
- 三个短期验收timer已自动触发真实采集并结束，正式timer也已触发成功。当前下一次日历触发为2026-11-09 16:10。没有重启整台主机或宣称已取得多日可用率。

run_scheduled.py为每次执行创建不可覆盖的reports/operations目录，保留开始记录、stdout/stderr、结果与manifest；当前运行状态在site/operation_status.json。失败保留上一次成功信息；孤立未完成记录保留并在下一次监督中报告，不能冒称失败前账户一定未发布。并发监督被锁拒绝；既有管线锁继续保护账户。运行中超过15分钟的页面记录会提示检查中断。

检查与维护：

```bash
systemctl --user status etf-research-daily.timer etf-research-daily.service
systemctl --user list-timers --all
journalctl --user -u etf-research-daily.service --no-pager
loginctl show-user ubuntu -p Linger
python scripts/verify_project.py
```

需要停用本项目后台任务时，先disable --now本项目timer，再stop本项目service；不要停止其他用户服务或整个user manager。更新代码前暂停本项目daily/health/archive三个timer，等对应正在运行的service完成，先增量取回并核对config/active_run.json、site/operation_status.json、reports/daily、reports/operations、reports/health、reports/notice-reviews、reports/notice-decisions、site/health_status.json及新快照；不能用旧Git归档覆盖未保存运行数据。代码/依赖检查通过后daemon-reload并重新enable --now本项目timer。

未发送邮件/微信等外部消息，不接实盘、不自动Git推送、不保存凭据。新的日报先存Ubuntu持久目录，后续交接由会话核验后提交GitHub。GitHub页面代码和状态文件是提交时快照，未验收公网实时托管。

## 本轮网络证据与边界

同一主机、域名和请求，IPv6 TCP约0.008秒连接，但TLS握手超时；IPv4证书验证正常，HTTP200约0.12秒。应用固定DNS解析IPv4解决已复现路径问题，不修改主机全局IPv6或证书设置。5轮完整真实采集（约17分23秒）全部准入；10次公告请求均200，55次总请求有5次搜狐503并保留后重试成功。因此这是有失败恢复证据的当日工程验收，不保证供应商永不故障，也不是多日运行结论。

2027年日历尚未在当前准入基线覆盖，跨年缺年会阻断，须新增独立官方证据和审阅。新公告仍须人工原文核对；不得自动重签旧目录、伪造行情或放宽条件。

参考：[curl地址族与HTTPS选项](https://curl.se/docs/manpage.html#-4)、[loginctl linger语义](https://www.freedesktop.org/software/systemd/man/254/loginctl.html)、[Python flock](https://docs.python.org/3.12/library/fcntl.html#fcntl.flock)。实际部署参数、触发及重启结果以reports/2026-11-06-operations中保存的主机证据为准。

## 运行闭环补充

新增独立健康观察、每日内容寻址归档和证据绑定公告审阅，操作及维护顺序见[闭环手册](OPERATIONS_CLOSURE.md)。维护时应同时管理本项目daily/health/archive三个timer；所有维护只针对本项目单位。动态health_status也须对照封存记录校验。
