# 本人回复分析与试验

默认流程已改为：自动抽样与身份回查 → 当前会话 AI 分析场景和状态 → 先保存生成回复 → 揭示历史答案 → AI 对照评价。用户无需逐条填写意图、对象关系或批准样本。页面用于查看结果和可选纠错。

继续使用 docs/wechat-decrypt-analysis 下的已有 CSV 和 SQLite，不重复导出全库。语义执行器是当前 Codex 会话中的 AI；Python 负责数据、校验、检索和页面，尚不包含独立模型 API。退出会话后不会自行持续分析或回复。

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

请求组合 auto_prompt.txt、风格档案、当前消息和最多 3 条开发组相似示例，由当前会话 AI 执行。检索使用中文双字片段和英文词重合排序，并按场景规则建议过滤；不是向量检索，最终场景仍由 AI 语义判断。无重合可不带示例，不从评测对照中检索答案。

已用一条虚构新消息检查请求构建、3 条开发示例检索和当前会话 AI 输出，保存在 request-smoke.json、request-smoke-result.json，不计入 13 条历史成绩。命令只构建请求，不会自行调用模型或发消息。

## 当前发现与下一步

主要差距是回复动作选择：该简单接收时重复解释，该确认字段时泛泛说查看文档，该等待协作方时过早安排动作。提示已据此修正，仍须用未见过的新样本验证收益。

有些原回复引入前文未出现的已完成工作、路况、身体感受等信息。历史风格不能补齐当前事实；应补取有效任务状态、媒体或已知日程，再决定回答，不能为了追求原文一致而猜测。

下一轮扩大闲聊、生活事务与情绪交流的可用证据，再做新的留出评测。独立语义模型执行器、实时上下文、应用页面及训练仍未接入；这些不妨碍当前会话继续自动分析。

## 验证与文件边界

- 22 项单元测试通过：含无需人工标志的流程、答案隔离、群聊说话人、时间边界、AI 依据、来源改动、跨组会话、冻结结果、防漏评、HTML 转义、开发组检索。
- Chrome 检查：13 张卡片、40 条分类依据、0 个填写控件、0 个页面错误；1200px 与 390px 视口无横向溢出，分类表可展开。另检查桌面截图。
- private 内真实样本、上下文、回复、风格证据、页面、截图和联系人映射均留本地。自动遮罩不保证完全匿名，残余业务事实、称呼等仍可能存在。
- analysis_output、exports 不提交。上级 /docs 整体忽略，只对精确源文件、测试、无真实内容提示词和 README 强制添加，不对整个目录强制添加。

## 保留的旧人工流程

reply_lab.py 与 review.html 保留旧的可选人工审核流程，用于明确意图的改写试验和本人评分。其 approved / privacy_reviewed / intent / object_type 门槛只作用于旧流程，不再阻塞 auto_lab.py。旧 review-scenes.html 保留原样，避免覆盖已经填写的内容。
