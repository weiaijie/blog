# website_v1

个人网站 V1 开发目录（按 `website_plan/` 执行）。

## 当前状态

- 已完成：离线脚手架、基础路由、核心页面骨架、通用组件、样式基线。
- 进行中：内容细化、交互完善、表单托管接入、部署流程联调。

## 对应计划文件

- `../website_plan/00_baseline/tasks.md`
- `../website_plan/01_home/tasks.md`
- `../website_plan/02_about/tasks.md`
- `../website_plan/03_skills/tasks.md`
- `../website_plan/04_projects/tasks.md`
- `../website_plan/06_contact/tasks.md`
- `../website_plan/07_tech/tasks.md`
- `../website_plan/08_design/tasks.md`

## 本地运行（网络可用后）

```bash
cp .env.example .env
npm install
npm run dev
```

Node 版本建议：`>=18`.

表单托管说明：
- 配置 `VITE_FORMSPREE_ENDPOINT` 后，联系表单会直接提交到托管服务。
- 未配置时，页面会提示“未配置表单服务”。

## 说明

当前环境无法访问 npm registry，因此暂未执行依赖安装与构建验证。工程文件已按 React + TypeScript + Vite + Tailwind 结构准备完毕。
