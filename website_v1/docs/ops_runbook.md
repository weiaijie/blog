# 运维操作手册（V1）

## 发布前检查

1. 执行 `npm run lint`。
2. 执行 `npm run build`。
3. 检查关键页面路由：`/`, `/about`, `/skills`, `/projects`, `/contact`, `/privacy`。
4. 检查环境变量：`VITE_FORMSPREE_ENDPOINT`, `VITE_BASE_PATH`。

## 发布流程

1. 推送到 `main` 分支。
2. GitHub Actions 执行安装、lint、build、deploy。
3. 部署完成后验证页面可访问。

## 回滚流程

1. 选择最近稳定提交。
2. 执行 `git revert <commit>` 并推送 `main`。
3. 等待 Actions 自动重新部署。
4. 复检关键页面和表单状态。

## 监控建议

- 前端错误：Sentry（V2可接入）。
- 可用性：UptimeRobot 或同类服务。
- 访问统计：GA 或 Plausible。
