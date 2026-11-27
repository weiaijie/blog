# 独立研究证据批次的 GitHub 发布准备

每次夜间封存后，先核对已公开目录是生产导出链的完整前缀，再按顺序准备缺少的批次。工具按清单逐项复制并校验新批次，只写入明确指定的独立目录。已公开条目保持原样，新目录追加原始回执、证据包和更新后的公开目录。定时器和 Git 发布继续各自读取实际回执。

在 Ubuntu 上，以 GitHub 同步后的项目为起点运行。

```bash
work=$(mktemp -d)
PYTHONPATH=src python scripts/prepare_observation_publication.py \
  --spool "$HOME/projects/etf-research-observation-exports" --output "$work/prepared"
```

当前公开目录已齐时输出 `up_to_date`，准备目录不生成。存在增量时，`preparation.json` 记录原目录 SHA256、新链尾和待发布批次。发布时先核对 Git 当前目录仍符合该原哈希，再将准备目录内 `reports/research-observation-publication/` 的增量和新目录合入同一路径。完整核验合并后的公开证据，提交后从 GitHub 读回。该路径已为原始批次关闭 Git 换行转换，保证回执和对象可按原哈希复验。

## 实测

11 月 28 日 03:19，Ubuntu 已封存的批次与 GitHub 一致，准备工具没有生成待发布目录。隔离演练从原基础包的目录开始，使用 11 月 27 日 22:20 的真实定时批次生成待发布内容。回执字节、证据清单与 GitHub 已有原件相同。用新目录恢复 683 个台账文件后，11 月 27 日单日报告与生产按当时的公开水位逐字段相同。 [核验结果](verification.json) · [公开链核验与恢复](../2026-11-28-observation-publication-catalog/README.md)
