# 跨年交易日历巡检的运行健康

工作台和 Agent 的「独立研究运行健康」新增交易日历巡检。健康检查读取 Ubuntu systemd 的计划、触发和退出，区分等待、漏跑、失败以及正常退出。日历证据页继续按归档核验交易所公告及其准入情况。

11 月 28 日北京时间 03:50 用新版健康检查读回 Ubuntu 的真实定时器和服务。十项任务中，交易日历巡检处于等待，下一次为 08:05。配置还包含 21:35 巡检。隔离测试分别覆盖计划前等待、到点漏跑、按时触发但退出失败三种情况，并确认失败进入同一份健康记录。

工作台在[独立研究](http://10.1.1.120:18766/workbench/#/policy)展开「独立研究运行健康」。Agent 使用 `GET /api/v1/research/observation/runtime-health` 查看 `jobs.calendar-watch`。日历公告和准入结果可另查 `GET /api/v1/research/observation/calendar-watch`。
