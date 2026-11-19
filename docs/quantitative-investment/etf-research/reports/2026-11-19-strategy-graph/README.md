# 策略中心的二维关系图

工作台「策略中心 → 打开二维关系图」使用 Cytoscape.js 3.35.0。用「定位节点」选择因子、模型或实验，点击图上相邻节点继续探索。每个模型都能用台账里的参数回放。实验详情提供看板入口与固定 Git 提交上的报告。选择结果写入链接，可直接分享，例如 `/workbench/#/catalog/graph?node=factor:adx`。

6 个因子、11 个台账条目（7 个境内模型和 4 个基准）、8 项归档实验，共 25 个节点、40 条关系。120 日趋势有两种用法，单趋势模型按月择时，三因子模型及其变体拿它投一票。量价、KDJ、ADX 分别是独立变体的额外确认条件。固定配置和市场基准只连接其实际对照实验。

Agent 读取 `GET /strategy-catalog.json`。已有 entries 继续提供计划和固定历史统计。graph.version 为 1，graph.edges 的方向为「因子 → 台账条目 → 实验」。entry 节点的 id 对应 entries[].id；experiment 节点的 view、url 分别指向可操作实验与报告。例：

```sh
curl -fsS http://10.1.1.120:18766/strategy-catalog.json | jq '
  .graph as $g
  | $g.edges[] | select(.source == "factor:adx") | .target as $model
  | {model: $model, experiments: [
      $g.edges[] | select(.source == $model) | .target as $id
      | $g.nodes[] | select(.id == $id) | {label, view, url}
    ]}'
```

节点和边由台账生成脚本、固定模型规则与已归档实验生成。股债比例、数据版本和成本沿用各条目的回放计划。桌面 Chromium 1366px 用 ADX，移动触摸模拟 390px 用 KDJ，分别实际点选画布节点，检查报告、实验入口、回放模型和首日请求一致性。
