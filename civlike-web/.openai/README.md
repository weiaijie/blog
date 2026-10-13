# Sites 公开预览

## 当前站点

- 固定站点地址：https://civlike-terrain-lab.prettyhawk1.chatgpt.site
- 地图入口：https://civlike-terrain-lab.prettyhawk1.chatgpt.site/?view=terrain-world&assetSeed=221648817&season=bloom
- 站点 ID：`appgprj_6acc56a15ad08191a8f8358942d686ef`，以 `hosting.json` 为准，不要重复创建站点。
- 访问范围：2026-10-13 重新读取确认是 `public`，保持公开；首次创建时为私有的记录仅属历史。
- 模型库入口：https://civlike-terrain-lab.prettyhawk1.chatgpt.site/?view=map-elements
- 2026-10-12 首次部署成功：`appgdep_6acc585873008191a78f1bedb8191ba1`。
- 首次发布的 Sites 源码提交：`16d5d0699966b1467b67756872a46602878f8bff`，对应原仓库地图代码版本 `3077f51`。
- 验证：隔离源码构建成功；在线浏览器显示 217 个区块的三维地图，季节时间持续推进。未将此检查视为完整性能或移动端验收。

## 更新边界

- `civlike-web` 是开发源码；`.sites-preview/` 是独立 Git 发布镜像，不要只在镜像里修改业务代码。
- `.sites-artifacts/` 保存临时发布包和截图；两个目录均已被原仓库忽略。
- 镜像仅包含网页配置、源码、测试、脚本与运行资产；不复制仓库其他项目、个人文档、缓存、验收截图或 `src/render/assets/source/` 下的 Blender 工程。
- 公开提供的静态产物只有 `dist/`。Sites 源码保存与网页产物发布是两个步骤。
- 原 GitHub 仓库 `weiaijie/blog` 的 `codex/map-visual-animation-track` 已于 2026-10-13 按授权推送到 `84a6642`（本轮后续资产提交另见 Git 历史）。没有配置 GitHub 自动部署，也没有把编码任务迁到 Codex Cloud。
- 现有 Cloudflare `blog` 项目及 `blog.weiaijie.top` 未修改。

## 后续发布

1. 在开发源码中完成修改和验证；本地 Blender 修改应先导出 GLB、贴图，再更新网页运行资产。
2. 用 Sites 工具读取当前站点及访问范围，获取该站点短期源码凭据。凭据只通过隐藏 stdin 传入官方 source helper，不写入文件、Git 或日志。
3. 使用 Sites skill 的 source helper 打开或恢复站点源码，核对并同步本项目文件，保留站点 ID 和已有源码历史。
4. 检查 diff 并使用中文提交说明保存发布源码；构建后由 source helper 推送到 Sites 自有源码仓库并打包。这不是向原 GitHub 仓库推送。
5. 保持已确认的公开范围，用 `save_site_version` 保存 helper 返回的同一提交和归档，再用 `deploy_site_version` 发布已保存版本；若版本已经保存，则复用该版本，不重复保存。
6. 等待部署状态 `succeeded`，用返回的实际 URL 检查地图；后续版本复用固定站点地址。

Windows 注意：使用 Git for Windows 的 Bash，不使用 WSL。若包装器调用 npm 时错误解析路径，先在隔离目录通过 PowerShell 运行 `npm run build`，再传 `commands: []` 打包已完成且源码未变的构建。打包进程设置 `TAR_OPTIONS=--force-local` 并使用正斜杠绝对归档路径，避免 GNU tar 把 Windows 盘符当作远程主机。

## 2026-10-13 第 2 版发布

- GitHub 远端核对提交：`84a66429688434403b7bd51c13c13353dea91a4d`。推送前当前分支领先 35、落后 0，无需合并。云端快照 `70ebd6e` 的应用源码与旧基线 `5fcd8f1` 一致，没有额外功能改动。
- Sites 源码提交：`24c4b43ea6766dd10fc2e157c1e550eb801242cf`；部署：`appgdep_6acdfc762a108191a2fe74552742eb46`，平台返回 `succeeded`。
- 上线 97 类独立资产、106 个模型版本。504 项测试及生产构建通过；公开 URL 上建筑工、居民和工程师完成动作、暂停、三视图、320/390 手机检查，页面错误和截图重试均为 0。
- 发布包仅含静态产物和托管清单，没有 Blender 源文件、其他项目或个人文档。原有 Three/OrbitControls 大分块警告仍在，不代表已经通过 200 格资产混合性能验收。
