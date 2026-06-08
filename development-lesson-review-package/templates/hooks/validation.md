# Global Validation Hooks

本文件用于记录工作完成前应执行的确定性检查。

## Default Checks

- 确认修改文件限制在请求范围内。
- 确认持久指导写入了正确层级：
  - 偏好写入 `AGENTS.md`
  - 工作流写入 `skills/`
  - 状态写入 `vault/`
  - 失败回归案例写入 `evals/`
  - 权限边界写入 `rules/`
  - 校验检查写入 `hooks/`
- 确认临时文件没有放进交付物目录。
- 确认写入会被日常任务默认读取的文件前，已评估上下文成本。

## Background Review Check

对每个已完成工作项，只提取足够通用、能帮助未来开发的经验：

- 重复出现的用户偏好 -> 更新 `AGENTS.md`。
- 重复执行的流程 -> 优先更新已有相关 `skills/`，没有合适承载点时才创建新技能。
- 当前持久决策和已知上下文 -> 更新 `vault/`。
- 具备可复现触发条件的错误或回归 -> 更新 `evals/`。
- 权限、安全或访问期望 -> 更新 `rules/`。
- 能提前发现问题的确定性检查 -> 更新 `hooks/`。

## Background Review Noise Gate

写入持久指导前必须先通过降噪门槛。默认策略是宁可漏掉弱经验，也不要把噪声写进长期记忆。

允许直接写入持久层的高置信度经验必须满足以下条件之一：

- 同一偏好、流程、失败模式在多次对话或多次任务中重复出现。
- 用户明确要求“记住”“以后都这样”“写进 `AGENTS.md`”“做成 `skill`”或等价表达。
- 某个遗漏造成明显错误、返工、误操作或错误结论，且未来有较大复发可能。
- 内容是稳定权限、隐私、路径、禁止操作、生产环境限制等边界。
- 经验能转成确定性检查、回归样例或固定流程。

以下内容默认不写入持久层：

- 单次任务里的实现细节。
- 一次性的用户表达习惯或临时偏好。
- 没有复发迹象的小偏好。
- Codex 自己的推测或未验证结论。
- 某个仓库的临时状态。
- 普通成功流程中没有新信息的步骤。
- 已经存在的同义经验。
- 只对当前 PR、当前 bug、当前临时上下文有用的信息。
- 太宽泛的空泛建议，例如“要认真检查”“注意测试”。

写入前必须回答这些自检问题：

- 这条经验是否跨未来任务有用？
- 它是否来自重复信号、用户明确要求、明显返工/错误、稳定边界，或可确定性验证的问题？
- 它是否已经选择了最窄的合适层级，而不是不必要地写入全局层？
- 它是否已在目标文件或 `lesson-review-log.md` 中以相同/近似形式存在？
- 如果删除这条经验，未来是否真的更容易再次犯错？

只有前两项为“是”、层级选择足够窄、查重通过，并且删除后确实更容易复发时，才允许直接写入持久层。中置信度线索只写入 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-candidates.md` 等待人工审查；低置信度线索不写入，只在本次中文总结里说明跳过原因。

## Context Budget Check

写入任何会被日常任务默认读取的文件前，必须评估上下文成本。高频上下文文件包括 `AGENTS.md`、触发到的 `skills/*/SKILL.md`、当前仓库项目指导文件和自动化 prompt。

- `AGENTS.md` 只写短小、稳定、可复用、能改变未来行为的规则；不要写历史、案例、长解释、审计记录或候选内容。
- 全局 `AGENTS.md` 建议控制在 1500-2500 字以内；项目 `AGENTS.md` 建议控制在 1000-2000 字以内。
- 如果新增内容会让 `AGENTS.md` 明显增长，优先合并或压缩已有规则，而不是追加新段落。
- 如果同类规则已超过 3 条，优先压缩成一条更抽象但可执行的规则。
- 写入 `skills/` 前必须先查找已有相关 skill；能迭代已有 skill 时优先更新已有 skill，不要因为同类经验创建重复 skill。
- 只有没有合适承载点，或新流程的触发条件、步骤和校验都明显独立时，才创建新 skill。
- 长流程不要全部塞进 `SKILL.md`；`SKILL.md` 只写核心流程和何时读取参考，详细内容放入 `references/`。
- 历史、案例、解释、审计记录、候选内容和长期状态放入 `vault/`、`evals/`、`hooks/` 或 skill references，按需读取，不进入默认上下文。

## Sensitive Information Check

自动复盘不得把敏感信息写入任何持久文件。

- 禁止写入 token、密钥、密码、cookie、授权头、私钥、证书、完整连接串、完整内部接口参数、客户/用户隐私数据。
- 禁止记录敏感原文；如需沉淀经验，只写抽象规则，例如“不要输出密钥内容”。
- 发现疑似敏感信息时，只在本次总结中说明“发现疑似敏感内容，未写入”，不要写入日志、候选或长期规则。
- 写入前应检查常见敏感关键词：`token`、`secret`、`password`、`passwd`、`Authorization`、`Bearer`、`cookie`、`private_key`、`AKIA`、`BEGIN PRIVATE KEY`。
- 如果无法判断某段内容是否敏感，按敏感处理，不落盘。

## Long Timeline Maintenance Check

长期项目需要定期整理自动复盘材料，避免日志、候选和规则无限增长。

- 候选经验必须包含状态、作用范围、复查时间或过期条件。
- 候选状态使用：待审查、已采纳、已拒绝、已过期。
- 作用范围使用：全局、当前仓库、当前模块、当前任务。当前任务范围默认不写入长期层。
- 中置信度候选超过 60 天仍未采纳时，默认标记为已过期；如果后续出现新证据，可以重新创建候选。
- 每月进行一次压缩整理：汇总上月日志、清理已拒绝/已过期候选、合并重复经验、把稳定流程整理进 `skills/`、把失败案例整理进 `evals/`、归档旧日志。
- 旧日志和旧候选按月份放入 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/archive/`，当前文件只保留最近 1-2 个月便于审查。
- 自动复盘可以提出“建议删除”“建议降级为候选”“建议从全局迁移到项目本地”，但不要自动执行删除或迁移，除非用户明确确认。
- 提出删除、降级或迁移建议时，必须写入 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-pending-changes.md`，使用待确认变更模板，等待人工确认。
- 月度整理时必须检查规则冲突：全局 `AGENTS.md` 与项目 `AGENTS.md` 是否矛盾，`skills/` 与 `hooks/` 是否重复或冲突，项目规则是否应覆盖全局规则，旧规则是否已过期。

复盘前先读取 `{{CODEX_HOME}}/automations/development-lesson-review/memory.md` 中最新主游标。维护面板读取 `memory.md`，并展示 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-cursor.json` 作为机器可读副本。只处理游标之后的新输入：

- 跟踪文件元数据已变化的 Codex 对话/会话记录。
- `last_seen_head` 之后的仓库提交。
- 状态哈希不同于 `last_seen_status_hash` 的工作区状态变化。

不要添加一次性事实、私有推理、猜测性规则或重复经验。写入前检查目标持久文件和 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-log.md`；如果相同或实质等价的经验已经存在，不再新增条目。

后台复盘只要修改了任何持久指导文件，就向 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-log.md` 追加一条简洁中文记录，包含来源、变更文件、经验、分层决定和校验。如果没有持久文件变更，不追加日志条目。

每次复盘结束后，把新的主游标写入 `{{CODEX_HOME}}/automations/development-lesson-review/memory.md`，包含本轮已复核到的时间、文件元数据摘要、仓库 head/status、是否发现新长期经验。只要 memory 主游标写入成功，就视为自动化游标已推进，避免旧输入被反复扫描。同步 canonical cursor `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-cursor.json`，并报告 canonical cursor 写入结果。只有 memory 主游标写入失败时，才报告自动化 cursor 无法推进；此时不要写入新的长期经验，避免重复沉淀。

## Pending Change Template

自动复盘提出删除、降级或迁移建议时，使用以下模板写入 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-pending-changes.md`：

### YYYY-MM-DD HH:mm - 简短标题

- 建议动作：删除 / 降级为候选 / 从全局迁移到项目本地
- 原文件：
- 原内容摘要：
- 建议目标：
- 理由：
- 风险：
- 确认状态：待确认
- 处理结论：
- 处理时间：

## Hook Template

### Check Name

- 命令：
- 适用场景：
- 通过条件：
- 失败动作：
