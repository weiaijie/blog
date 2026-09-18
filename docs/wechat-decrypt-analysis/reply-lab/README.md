# 本人回复分析与试验

现已提供本机回复草稿台：输入对话 → 独立 Codex CLI 生成 → 查看依据与缺口 → 复制草稿。另有自动抽样、身份回查、先冻结生成再揭示答案的评测管线，无需本人整理样本表。

继续使用 docs/wechat-decrypt-analysis 下的已有 CSV 和 SQLite。2026-09-18 起 app.py 与 replay_trial.py 可通过本机已登录的 Codex CLI 调用模型；原 auto_lab.py 的分析路径仍由当前会话 AI 执行。服务运行后可以独立生成草稿，不依赖本会话代写结果；不自动监听微信或发送消息。

## 当前入口：本地回复草稿台（2026-09-18）

在本目录运行 `./启动回复草稿.ps1`，或 `python app.py --port 8765`，打开 http://127.0.0.1:8765/ 。需要已有 Codex CLI 登录；无需另填 API 密钥。默认 CLI 模型由安装版本选择，未固定精确模型版本；本工具独立进程不加载用户 config、项目指令、工具、插件或记忆。

- 输入可以是对方消息，也可以是带“我：”“对方：”的多行对话；未标新角色的换行延续上一位说话人。
- 生成时会把必要、经过机械遮罩的片段和风格参考发送给 Codex 模型服务，仍可能保留业务或个人信息，不是完全匿名或离线推理。
- 有依据才写当前进度和本人状态，历史示例只参考说话方式。缺事实可能只返回缺口；不能要求模型猜测本人实际决定。
- 默认输入和结果只在内存（最多保留 20 次生成，关闭服务清除）；点击“保存到本机”才把该次资料、草稿和修改写入 private/feedback，不自动用于训练。
- 历史回放选择会自动填入 13 段新记录，按当时的时间生成，原答案不传给生成器。编辑回放文字会退出回放模式；此时编辑后的文字作为本次输入，页面有提示。
- 49 项单元测试通过；7 个合成机制案例通过 AI 内容复核；真实页面生成、复制和 320/390/1200px 检查通过。

[完整计划](../../../个人/模拟自己说话推进计划.md)、[本版验收与限制](本地草稿工具验收-20260918.md)、[新 13 条历史对照](private/replay-20260918/results.html)。技术闭环已完成，模仿质量仍为试验状态；本轮没有把自动评分当成本人认可。

新增程序职责：reply_engine.py 组织来源时间及输出校验，codex_provider.py 做文本模型调用，app.py/app.html 提供本地入口，replay_trial.py 冻结并验证历史回放，check_live_behaviors.py 显式运行联网的合成检查。`python -m unittest -q` 不调用模型；联网检查需单独运行并使用新输出文件。

历史回放命令：

~~~powershell
python auto_lab.py prepare --run private/new-active
python auto_lab.py prepare-eval-scenes --run private/new-scenes
python replay_trial.py prepare --out private/new-replay --batches private/new-active private/new-scenes
python replay_trial.py run --out private/new-replay
python replay_trial.py render --out private/new-replay
~~~

prepare-eval-scenes 从非开发联系人找场景线索，关键词不等于真实场景；生成与揭示步骤分别冻结校验，启动过的批次不重写。较早资料只取同一会话、目标回复之前最多 7 天且匹配当前话题的 6 条，并回查发送者；本轮只找到 3 条，不能声称已补齐当前事实。

## 2026-09-17：新样本评测与场景档案

已完成原先准备的 32 段：15 段学习、15 段生成对照、2 段信息不足；另外定向补取并分析了 9 段开发记录。合并旧开发样本后有 39 段风格参考，开发与本轮评测联系人交叉为 0。

本轮 AI 自评：15 条中表述贴近 9、偏长 2、不贴近 4；回应动作一致 5；历史核心意思一致 3、可兼容 2、不同 10。未标出新增事实或额外承诺，但不代表本人验收。口吻、回应动作和语义分开评价，且两轮样本不同，不能据此宣称准确率提升。

[新一轮结果与场景档案](private/review-20260917-next-sample-check/results.html)可直接查看，无需填写。[本轮说明](新样本评测与场景档案-20260917.md)记录了证据与缺口。旧首轮结果继续保留。

## 首轮自动结果：2026-09-17

- 数据来自既有历史快照，最新消息时间为 2026-03-14 14:28:17，不是实时微信。
- 从最近 180 天的活跃私聊和群聊抽取 40 段新候选，避开旧 69 段样本所在的会话日期。按整个会话隔离：18 段开发候选、22 段评测候选，交叉会话为 0。
- 本人及可识别发送者通过只读 SQLite 消息行和 Name2Id 回查；未知发送者仅保留媒体或系统缺失标记。身份核验不等于完全匿名。
- 补取目标回复前最多 24 条、30 分钟、3500 字的上下文；群聊保留不同说话人编号，媒体保留缺失标记，不臆造图片或语音内容。
- AI 逐条记录场景、状态、质量、置信度和前文依据。28 段可用：15 段学习、13 段生成对照；12 段因上下文或个人当时情况不足单列。另排除 2 个凭据候选、1 个纯非文字回复候选。
- 场景：工作 27、闲聊 2、生活事务 6、待判断 5。状态：正常回应 14、不确定 7、催促推进 2、待判断 17。以上是候选分布，不是日常聊天占比或分类准确率。
- 13 段生成后对照自评：表达贴近 3、偏长 7、不贴近 3；历史语义一致 1、可兼容 6、不同 6。发现 1 条额外架构要求、1 条过早安排动作。这是同一会话 AI 自评，不能合成为本人认可率。
- 生成对照只覆盖工作 11 段、生活事务 2 段；情绪交流、玩笑和不满等没有完成效果验证。

[当前结果页](private/auto-20260917-v2/results.html)共 13 张对照卡片，全部 40 段的分类依据与未生成原因可展开查看。没有必须填写的控件。

## 使用自动流程

Python 3 标准库即可运行，不导入会加载密钥的旧 MCP 模块。本机 Python 为 C:\Users\saber\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe。

以下在本目录执行，PowerShell 可把 python 替换为上述路径的调用：

~~~powershell
python auto_lab.py prepare --run private/auto-new
~~~

执行任务的 AI 读取 analysis-inputs.json，编写 ai-analysis.json。这是模型输出步骤，不是用户填写步骤。开发组可见原回复；评测组没有原回复，场景和状态只看目标之前的上下文。格式和校验见 validate_analysis：

- 顶层：input_sha256、reviewer_kind 为 ai、reviewer、items。
- 每项：id、scene、reply_state、quality、confidence、reason、evidence_indices。
- quality 为 usable / insufficient / excluded；confidence 为 high / medium / low。
- 依据为从 1 开始的上下文索引；非待判断的本人状态还需 state_evidence_indices，且只能引用本人前文。
- 可用评测项需要 draft 字符串数组。不得从目标答案提取意图再冒充自主预测。

~~~powershell
python auto_lab.py assemble --run private/auto-new
~~~

此步核验来源、输入哈希、身份和会话划分，输出学习集、隐藏答案的评测输入、生成回复、对照和冻结清单。已冻结目录不能重新生成；改提示后应用新批次，不能事后覆盖原回复再重算成绩。

AI 此时才读取 comparison.private.json，生成 ai-evaluation.json。顶层声明 comparison_sha256、AI 来源和完整 items；每项含 id、style（贴近/偏长/不贴近）、meaning（一致/可兼容/不同/无法判断）、布尔值 unsupported_fact 和 extra_commitment、verdict、reason。

~~~powershell
python auto_lab.py evaluate --run private/auto-new
python auto_lab.py render --run private/auto-new
~~~

评价核验完整 ID、输入版本和生成后未修改，并按场景、状态汇总。字面不同不自动算事实错误；相似短句也不等于选对了回应动作。

## 新消息试用入口

首轮 style-profile.json 记录共通表达习惯、工作/闲聊/生活事务差异、证据不足的状态和改进规则。它在首轮复盘后形成，用于后续请求，不能声称已用于首轮盲测。

~~~powershell
python auto_lab.py request --run private/auto-20260917-v2 --message '接口字段我改好了，文档也更新了，你看下。' --out private/auto-20260917-v2/request-new.json
~~~

请求组合 auto_prompt.txt、风格档案、当前消息和最多 3 条开发组相似示例，由当前会话 AI 执行。检索使用中文双字片段和英文词重合排序；场景规则建议只加权、不直接排除候选，避免混合话题丢失有效示例。不是向量检索，最终场景仍由 AI 语义判断。无重合可不带示例，不从评测对照中检索答案。

已用一条虚构新消息检查请求构建、3 条开发示例检索和当前会话 AI 输出，保存在 request-smoke.json、request-smoke-result.json，不计入 13 条历史成绩。命令只构建请求，不会自行调用模型或发消息。

## 当前发现与下一步

主要差距是回复动作选择：该简单接收时重复解释，该确认字段时泛泛说查看文档，该等待协作方时过早安排动作。提示已据此修正，仍须用未见过的新样本验证收益。

有些原回复引入前文未出现的已完成工作、路况、身体感受等信息。历史风格不能补齐当前事实；应补取有效任务状态、媒体或已知日程，再决定回答，不能为了追求原文一致而猜测。

下一轮扩大闲聊、生活事务与情绪交流的可用证据，再做新的留出评测。独立语义模型执行器、实时上下文、应用页面及训练仍未接入；这些不妨碍当前会话继续自动分析。

## 验证与文件边界

- 当前共 34 项单元测试通过：除原先 29 项外，增加开发补样排除评测联系人、提示版本冻结、补充示例检索、动作评价独立性、本人排期状态依据的检查。
- 新结果页 Chrome 检查：15 张卡片、32 条分类依据、分场景档案及动作评价可显示、0 个填写控件、0 个页面错误；1200px、390px、320px 展开内容后无横向溢出。
- private 内真实样本、上下文、回复、风格证据、页面、截图和联系人映射均留本地。自动遮罩不保证完全匿名，残余业务事实、称呼等仍可能存在。
- analysis_output、exports 不提交。上级 /docs 整体忽略，只对精确源文件、测试、无真实内容提示词和 README 强制添加，不对整个目录强制添加。

## 保留的旧人工流程

reply_lab.py 与 review.html 保留旧的可选人工审核流程，用于明确意图的改写试验和本人评分。其 approved / privacy_reviewed / intent / object_type 门槛只作用于旧流程，不再阻塞 auto_lab.py。旧 review-scenes.html 保留原样，避免覆盖已经填写的内容。

## 两轮复核修正：2026-09-17

[复核记录](复核记录-20260917.md)记录问题、修复与实际检查结果。

- prepare 自动汇总 private 下各批 source.private.json 和 candidates.json，排除已使用的会话日期及原始消息来源；保留历史开发/评测分组，冲突直接报错。无新候选时报错，不退回已见样本。保留这些本地历史清单才能维持跨轮去重，其他目录的批次不会自动发现。
- 未知发送者的文本只留占位符，不归给本人或对方；媒体缺失仍保留标记。
- render 无论是否已有评价都核验冻结输入和生成结果；摘要重新计算，评价汇总必须与逐条评价一致。
- 只要已经写出生成回复或对照，就不允许重跑覆盖，包括写盘中断、冻结清单未生成的情况。此类残留结果需要保留并使用新批次继续。
- 当时新抽样验证得到 32 段（开发/评测候选各 16），与旧批次会话日期重叠 0、原始消息重叠 0、历史分组改变 0，身份回查 32/32。后续已完成语义分析和 15 条生成评测，见本文最新进展。
- 原 13 条生成与评价保留不变。本次修复的是流程正确性，不代表口吻效果提升。

## 定向开发补样与版本记录

~~~powershell
python auto_lab.py prepare-scenes --run private/scene-dev-new
~~~

此命令在历史快照最近 365 天内，从本人有互动的私聊检索情绪、闲聊、生活关键词候选；排除已归入评测的联系人，补样全属开发组。关键词只用于找资料，最终必须由 AI 看上下文分类。本轮检索得到 9 段，语义分类实际为工作 5、生活事务 3、闲聊 1，不能把检索线索直接当标签。未取得足够情绪交流证据，未声称已覆盖。

本轮在读取评测答案前保存 generation-context.json，包含实际使用的提示、风格档案和 39 段开发示例；ai-analysis.json 通过 generation_context_sha256 绑定版本，assemble、render、evaluate、request 都校验。示例必须是开发组，且不得与本轮评测联系人交叉。后续 live auto_prompt.txt 加入了本轮反馈，不回算本轮成绩。

新消息请求可用下列入口，并检索冻结记录中的补充开发示例；通用语气片段如“了吗”不会单独引入无关例子：

~~~powershell
python auto_lab.py request --run private/review-20260917-next-sample-check --message '停车位搞定了吗' --out private/review-20260917-next-sample-check/request-new.json
~~~

新增 action_alignment（一致/不同/无法判断）与 information_gap（无/当前任务进度/系统知识/个人事实/指代或媒体/隐含意图）评价维度。两者可同时省略以兼容旧结果；一旦提供必须覆盖全部生成项。状态新增排期紧张，仅用本人明确文字支持，不将他人赶时间视作本人压力。
