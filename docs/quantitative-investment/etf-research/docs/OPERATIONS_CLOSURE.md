# 运行健康、归档恢复和公告审阅

本文件对应OPERATIONS_CLOSURE_PLAN.md。仅研究，不修改冻结引擎或准入规则。所有命令在项目目录使用已配置Python执行。

## 独立健康观察

```sh
python scripts/check_health.py
python scripts/check_health.py --record
systemctl --user status etf-research-health.timer etf-research-health.service
```

健康timer每15分钟运行，独立于采集服务。输出为reports/health/唯一ID/result.json及manifest，原子更新site/health_status.json。报告告警仍是成功完成检查，不触发重启风暴。页面显示观察时间；超过30分钟视为陈旧，不能称实时正常。整台主机关机或网络不可达仍需要外部观察者，本轮没有发送外部提醒。

交易日历按上海时区核实；采集时点16:10/16:40/17:10各留20分钟宽限。旧成功记录不能掩盖新时点漏跑，休市不能掩盖前一交易日积压。16分钟仍在运行显示中断/超时。日历缺年、账户完整性失败、定时器停用、采集失败、公告待审均可见；审核记录完整也不自动解除准入阻断。

归档状态同时检查timer/上次服务结果及本机归档完成回执；回执超过26小时提示陈旧。回执是上次创建成功的记录，不能代替日后对全部存储对象重新校验。

## 增量归档

固定基线为config/archive_inventory.json中的Git公开文件；追加data/snapshots、reports/daily、reports/operations、reports/health、reports/notice-reviews、reports/notice-decisions及三个活动指针。任何新增静态代码/文档需更新清单；无关未跟踪文件不自动进入归档。运行目录出现隐藏/未知扩展文件会阻断，缓存排除。绝不扫描用户主目录、.env、.ssh或Git凭据。

默认存储为独立Ubuntu的/home/ubuntu/projects/etf-research-evidence-archive；与运行项目分开。每日17:45定时归档，激活后60秒补一次，失败120秒重试、20分钟最多3次。正常休市仍归档健康记录。对象按SHA256去重，每份快照包含完整文件清单，不依赖前一份清单；需要保留它引用的所有objects。不会删除旧对象或做保留期清理。

定时整库归档用 `--compress-manifest` 把新清单保存为 `<ID>.json.gz`，历史 `<ID>.json` 仍可直接读取。验证、恢复和比对命令按解压后原始字节核对 SHA256。跨主机复制保留原文件名和字节。

```sh
python scripts/archive_evidence.py capture --store /home/ubuntu/projects/etf-research-evidence-archive
python scripts/archive_evidence.py verify --store /home/ubuntu/projects/etf-research-evidence-archive --snapshot <64位快照ID>
python scripts/archive_evidence.py compare --store /home/ubuntu/projects/etf-research-evidence-archive --snapshot <ID> --destination <待比较目录>
python scripts/archive_evidence.py restore --store /home/ubuntu/projects/etf-research-evidence-archive --snapshot <ID> --destination <不存在的新目录>
```

capture顺序取得归档、调度、管线、审阅、健康锁；锁占用则本轮失败保留，由服务有限重试。逐文件读取并二次核验文件集合和内容；对象先写临时文件并fsync，再用独占硬链接发布完整对象；清单fsync后才回报成功，完成回执在同一组锁内写入。中断可能留下未引用对象，后续验证重用，不删除、不冒称完整快照。

restore先校验清单自身哈希及全部对象，再写新目录，逐文件读回。已有目录一律拒绝，即使内容相同也不合并；compare仅列新增/冲突/相同，不写入。恢复中断保留不完整新目录，下次换另一个新目录。恢复不启动systemd、不切换生产账户、不复制锁状态。恢复后应执行verify_project.py、基础测试和离线复现，再人工安排接管；本轮只做隔离演练，没有接管现有服务。

同机归档不防整机磁盘损坏。跨主机取回时复制objects和snapshots至新的接收目录，使用verify命令核验指定ID，再比较/恢复；本轮实际做Windows副本核验。跨Windows/Linux传递对象清单时用文件保持LF字节，不使用会引入CR的文本管道；复制后必须运行verify，不能只信管道最后一个进程的退出码。未来取回不会自动发生，也无自动Git推送。公开GitHub只保存代码、运行证据和验收摘要，不重复提交整个内容寻址对象仓。

## 公告待审与审核记录

每日准入遇CatalogChanged会保存failure.json和notice_review完整包，并继续失败。两ETF的所有目录变化在包内并列；失败生成包的原因也保留。标题分类只是提示，不是最终事项判断。

```sh
# 新输出目录，不覆盖旧包；下载原文同样保存每次失败及SHA256
python scripts/review_catalog.py --snapshot <候选快照名> --output reports/notice-reviews/<新ID> --download-evidence
# 将包内decision_template.json复制到工作文件，逐项填写后提交记录
python scripts/review_catalog.py --packet reports/notice-reviews/<ID> --decision <已填写审核JSON>
```

结论只有no_account_effect、requires_event_or_rule_update、unresolved。前两者要求确认完整原文、证据路径+SHA256+页码/段落、理由；生效日期按原文逐项填写。证据可以包含原PDF及已保存的提取文本；审核工具校验绑定与完整性，不能自动证明人工理解正确。不得填写姓名、账号等私人资料。

记录写入不可覆盖reports/notice-decisions；同一变更追加记录，按实际UTC记录时间取最新，旧结论保留。审核结果绑定包及变更指纹，不能套到新修订公告。公告撤下不自动取消分红；下载失败、缺原文、仅看标题不得标为已核验。

每日准入仍以原官方目录为基线。11 月 27 日核准的两个无账户影响条目通过 `reviewed_catalog.py` 校验完整变更指纹、封存审阅决定和正式 PDF。目录出现未核准新增、修改或撤下时仍会阻断。发现新分红、份额或停复牌事件时，另建证据版本，审核事件及生效日后重新核对旧账本前缀。

补跑已结束的交易日可使用原始行情和收盘快照。本次按 24、25、26 日逐日处理。每次使用上一日已发布的检查点，生成新日报后再用 `check_session_transition.py --bundle` 核对。运行记录以 `offline_recovery` 标识。

```sh
python scripts/run_scheduled.py --through 2026-11-24 \
  --candidate 20261124T171408-7f824d0c-prices \
  --official 20261124T171408-7f824d0c-official
```

## 维护顺序

更新前暂停本项目daily/health/archive三个timer，等待对应服务结束；先取回新增证据及三个状态指针。核验后仅部署本轮变更，不能用旧Git归档覆盖运行数据；更新清单，执行完整性和必要测试，daemon-reload并恢复三个timer。不要动其他用户服务。恢复生产状态后检查enabled/active、linger以及各服务退出结果。

### 独立研究运行目录

独立研究服务及原 18 户的看板使用各自的运行目录。更新共享 Python 模块或配置时，根据 `systemctl --user cat` 的 `WorkingDirectory`、`ExecStart` 和覆盖配置，核对每个受影响的副本。将待部署提交的 Git 文件对象 ID 与运行文件的 `git hash-object` 逐个比对，并记录差异、部署提交和读回结果。

选择相关服务两次执行之间的维护窗口，确认服务已经退出。只同步核对过的代码和配置，保留独立归档、运行回执和公开证据导出目录。更新 unit 后用 `systemctl --user daemon-reload` 重新加载。检查 `FragmentPath`、`DropInPaths` 和下一次触发时间，随后按真实回执验收。归档读写模块变更后，使用实际运行目录的模块逐份核验已有归档清单和引用的对象。

技术参考：[systemd定时器](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)、[Python路径处理](https://docs.python.org/3.12/library/pathlib.html)。本轮以实际主机systemd-analyze和触发记录验收，不以配置文件存在冒称已运行。
