# 可自行运行的 ETF 回测

在内网看板打开「历史回测 → 自己运行回测」。选起止日期、本金、费用和调仓方式。四个输入框依次是沪深300（510300）、标普500（513500）、恒生（159920）和国债（511010）的相对份数。例如填入 3、1、0、6，目标仓位就是 30%、10%、0%、60%。点击「运行回测」后可以查看逐日回撤或总资产、最大回撤的前高和谷底、损失金额和恢复日期。结果下方提供可重新运行的设置链接与 JSON 下载。修改表单后须再次点击运行。

### Agent 调用

在看板同一主机使用 `GET /api/v1/backtest/options` 获取支持的日期、标的顺序、参数、费用档和默认值。将六个参数各传一次给 `GET /api/v1/backtest`。两端使用同一份模拟代码。下面是三地股票平分、国债一半的例子。

```sh
curl --fail-with-body 'http://10.1.1.120:18766/api/v1/backtest?start=2024-10-30&end=2026-10-30&capital=100000&weights=1,1,1,3&rebalance=monthly&fees=base'
```

离线运行时，从项目目录执行同一组参数。

```sh
python scripts/interactive_backtest.py --start 2024-10-30 --end 2026-10-30 --capital 100000 --weights 1,1,1,3 --rebalance monthly --fees base
```

JSON 返回 `parameters`、`symbols`、`summary`、逐收盘日的 `daily` 和含委托及实际模拟成交份额的 `orders`。精确小数以字符串表示，收益率、回撤按小数比例表示。负的 `max_drawdown` 表示从前高回落，正的 `peak_to_trough_loss` 表示这次回落的损失金额。未收复前高时 `recovery` 为空。参数错误返回 HTTP 400 和 JSON 错误原因。

### 数据与执行口径

使用四只 ETF 已共同核验的 2023-10-30 至 2026-10-30 历史数据。日期取请求区间内的首末交易日，至少需要两个交易日。起始为现金，首日收盘计算目标，下一交易日开盘模拟执行。可选每月重新平衡或仅初始建仓，使用同一套整手取整、现金、停牌、分红应收及到账条件。基准佣金万三、最低 5 元，单边滑点 5 个基点。低费用档为万一及 1 个基点，高费用档为千一及 10 个基点，各档最低佣金均为 5 元。期末按人民币收盘价估值。模型成交价可能超出当日交易区间，订单提供对应标志。操作区仅执行历史研究模拟。

参数表单参考了 [Portfolio Visualizer 的回测设置](https://www.portfoliovisualizer.com/backtest-portfolio)。独立命令及机器可读输出参考了 [QuantConnect LEAN 的命令行回测](https://www.quantconnect.com/docs/v2/lean-cli/backtesting/deployment)。

使用示例参数时，期末 110,836.53 元，最大收盘回撤约 6.80%。对照旧报告的四组两年逐日余额，另重放 5,828 个收盘记录、429 条订单及原有滚动统计，检查原文件内容一致。自定义金额、费用、单资产配置、休市端点、零回撤与无效请求由 tests/test_interactive_backtest.py 检查。
