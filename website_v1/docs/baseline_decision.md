# 基线决策记录（V1）

日期：2026-03-01

## 1. 范围

- V1：首页、关于我、技能、项目、联系方式。
- V2：博客能力（列表、详情、搜索、标签、评论、统计）。
- V3：自建后端/CMS/账号体系。

## 2. 技术栈

- 前端：React + TypeScript + Vite + Tailwind CSS。
- 路由：React Router。
- 代码规范：ESLint + Prettier。

## 3. 托管与发布

- 默认托管：GitHub Pages。
- 发布链路：GitHub Actions（build + deploy）。

## 4. 动态能力策略

- V1 不自建后端。
- 表单、评论、统计优先第三方托管服务。
- 默认候选：Formspree / EmailJS、Giscus / Disqus、GA / Plausible。

## 5. 完成定义（DoD）

- 移动端与桌面端布局正常。
- 核心交互可用（导航、跳转、表单提交流程）。
- 无阻塞控制台报错。
- Lighthouse Performance >= 80（移动端）。
- Lighthouse Accessibility >= 90。
- 无占位内容与 404 链接。
