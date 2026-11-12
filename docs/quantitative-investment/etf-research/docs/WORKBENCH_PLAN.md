# 统一量化工作台

## 目标与范围

2026-11-12：将已有计算能力整理为人工可操作、Agent可复算的工作台。新界面独立部署在 `/workbench/`，完成验收后作为 `/` 入口；旧 `/market.html` 和 `/backtest.html` 保留。冻结引擎、历史报告、原始快照和18户前瞻记录不因界面迁移改变。

五个页面：研究总览、行情与数据、模型回测、组合比较、研究报告。总览区分行情截止、回测截止和前瞻观察日数；报告页明确固定研究不受当前方案控制。

## 设计与技术

- 深蓝导航 `#17364a`、白色图表 `#ffffff`、蓝灰背景 `#edf2f5`、操作蓝 `#235e79`、选中标记 `#e5b758`。涨跌采用红涨绿跌，表格贡献保留正负号。
- 中文系统字体，不下载外部字体；数值使用等宽数字。桌面侧栏导航，手机横向导航；中央图表、方案与交易详情抽屉。图表旁必须保留日期选择，不能只能用鼠标点图。
- Vue 3单文件组件、TypeScript、Vite、Vue Router、Element Plus；Lightweight Charts维持5.0.9，不同时替换图表算法或回测引擎。生产构建与依赖锁入Git，运行主机无需Node。
- 页面按路由加载，初始不运行任何窗口研究；市场与选项请求共享。各视图使用实际API结果，不在前端重算收益或生成交易信号。

## 方案与Agent契约

`frontend/src/domain.ts` 定义版本1方案。字段为 version/name/start/end/capital/fees/rebalance/model/installments/portfolios；配比顺序固定510300、513500、159920、511010。

本机最多保存20个方案，同名更新，删除可撤销；JSON导入做类型、日期、数值、枚举和字段验证。保存只在浏览器localStorage，不自动上传到GitHub/服务器。跨设备使用JSON或复现链接；私密资料不应放入方案名称。

Agent请求清单包含方案和与界面相同的GET URL：配比回测、逐日起点、组合比较、所选模型回放、固定四方法及技术确认比较。每个接口沿用原服务端参数与准入校验。导出某个请求不代表选中区间已通过该模型准入。

固定配比和分批回放使用组合A；趋势与因子模型使用固定境内配比和调仓规则。配比比较使用1至3组权重及调仓设置，不使用回放模型选择。四方法/技术确认比较使用各自既定模型，不使用自定义权重。界面逐处标明，禁止悄悄用另一套参数冒充当前方案。

## 实施与验收

1. 新增前端工程与参数契约，保留所有旧API；构建静态清单白名单注册到Python服务。
2. 接入逐日回放、完整计算、K线与买卖标记、当日因子和订单。单步只请求当前前缀，不预取未来全部价格。
3. 接入配比、四方法、量价/KDJ/ADX一年/两年窗口；打开最差一期查看同区间曲线、当日交易及因子。配比比较额外提供整个持有期/所选组合峰谷期/逐日ETF与费用归因。
4. 验证保存恢复、分享与Agent清单；参数改变取消等待并使旧结果失效。对照旧接口JSON、统计表和归因金额；测试手机、键盘标签、错误与无样本状态。
5. 更新当前进度及原规划对照；更新静态清单和归档文件清单。暂停本项目定时器后部署，保留三个活动指针，验证后恢复。提交推送原分支并读回。

验收结果见 [工作台报告](../reports/2026-11-12-workbench/README.md)。工程验收不等于投资目标验证。

## 保留的边界与下一阶段

本轮不新增信号确认天数/分档仓位，不调参追求4%，不迁移尚有现金边界差异的Backtrader引擎。专题交互报告仍在旧页，通过报告目录打开；本轮不逐一重写所有专题图表。方案仅本机保存，无多设备账号同步；长计算不显示伪造的完成百分比。外部提醒、正式除息参考价、完整停复牌、可靠估值/基本面仍按原规划继续。

## 开发与复现

在 `frontend/` 使用Node 22.12以上：`npm ci`、`npm test`、`npm run build`。构建进入 `site/workbench/`。已提供Vite开发代理供Windows访问Ubuntu原API；生产使用Python `scripts/serve_market.py`。运行环境与原Python依赖锁保持一致。

浏览器验收：使用安装了Playwright及Chromium的Python执行 `frontend/tests/browser_checks.py --base <隔离地址> --baseline <旧API地址> --output <新报告目录>`。基准接口必须来自本次未修改的计算层，不能用模拟响应替代。

技术来源：[Vue/Vite](https://vuejs.org/guide/scaling-up/tooling.html)、[Vue Router](https://router.vuejs.org/introduction.html)、[Element Plus](https://element-plus.org/en-US/)、[Lightweight Charts](https://tradingview.github.io/lightweight-charts/)。
