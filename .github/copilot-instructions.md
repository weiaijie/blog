# Copilot 使用说明（针对本仓库）

目的：让 AI 编码代理快速理解仓库结构、常用工作流和变更边界，以便安全且高效地进行编辑与建议。

概览
- 本仓库为基于 Jekyll 的静态个人站点（站点源文件位于仓库根目录，生成输出在 `_site/`）。
- 主要源码位置：根目录的 Markdown 页面（如 `index.md`、`面试/`、`简历/`）、模板文件（`_layouts/`、`_includes/`）、静态资源（`css/`、`js/`）。
- 不要直接编辑 `_site/`：该目录为构建产物，应由 `bundle exec jekyll build` 生成。

关键文件示例
- 页面模板：`_layouts/default.html` — 控制 HTML 基本骨架（CSS、字体、脚本的引入）。
- 头部导航：`_includes/header.html` — 导航的 active 检测通过 `page.url contains '/about/'` 等 Liquid 表达式实现，修改菜单时请保持相同模式。
- 配置：`_config.yml` — site 元数据、排除项、markdown/highlighter（kramdown / rouge）。
- 依赖：`Gemfile` — 使用 `github-pages`，在本地尽量用 Bundler 来安装与运行以匹配 GitHub Pages 环境。

构建与本地开发（可复制的命令）
- 安装 Ruby 依赖（推荐，保证与 CI/GitHub Pages 一致）:
  - `bundle install --path vendor/bundle`
- 本地预览（开发）:
  - `bundle exec jekyll serve`  # 启动本地服务器并观察终端输出的构建/模板错误
- 生成静态文件（发布/检查）:
  - `bundle exec jekyll build`
  - 生产环境构建: `JEKYLL_ENV=production bundle exec jekyll build`

项目特定惯例与注意点（只记录可在代码中发现的规则）
- 资源路径：模板中使用 `{{ '/css/main.css' | relative_url }}`；为避免 404，新增静态资源请使用相同 `relative_url`/`baseurl` 约定。
- 页面 Front Matter：大多数页面包含 `layout: default` 与 `title`，添加新页面请包含 Front Matter。
- 导航激活：`_includes/header.html` 里用 `page.url` 判断高亮，添加新顶级路径时也要更新此处。
- 多语言/中文文件名：仓库中存在中文目录（如 `面试/`、`简历/`），请保留编码与路径一致性，GitHub Pages 可正确发布这些路径。
- 自定义域名：仓库根有 `CNAME`，不要删除，若更改域名需同步更新该文件。

与其他子工程的关系
- 仓库下包含若干独立子工程（例如 `app/`、`personal-website/`），它们使用 Node/Next 等不同堆栈：
  - 不要在修改 Jekyll 站点时同时更改这些子工程的依赖，除非你知道会如何联动。
  - 若需要运行子工程，切换到相应目录并使用其 `package.json` 中的说明（`npm install` / `npm run dev`）。

调试与常见问题线索
- 模板或 Liquid 错误：运行 `bundle exec jekyll build` 会在终端输出具体错误行号，优先修复构建错误后再检查浏览器问题。
- 资源 404：通常与 `_config.yml` 中的 `baseurl` / 模板中 `relative_url` 使用不一致有关。

拉取请求与变更边界建议
- 小而明确的提交：模板、样式、内容变更尽量拆分为独立 PR（例如：样式调整单独一个 PR，内容新增为另一个 PR）。
- 文案/内容改动：直接修改对应 Markdown 文件（根目录或子目录），不需要更改模板。
- 模板或布局更改：在 PR 描述中注明影响范围（例如：会影响所有使用 `layout: default` 的页面）。

如果不确定
- 首先在本地运行 `bundle exec jekyll build` 来验证修改不会破坏构建。
- 遇到跨子工程改动（例如同时改 `app/` 与站点模板），在 PR 描述中明确说明如何验证（命令、URL、期望行为）。

请反馈
- 我已把此文件写入 `.github/copilot-instructions.md`，如果有遗漏的本地脚本、CI 配置或特定分支策略，请告诉我以便补充。
