# Global Codex State

最后更新：{{DATE}}

## Current Context

- 全局 Codex 根目录：`{{CODEX_HOME}}`
- 全局指导文件：`{{CODEX_HOME}}/AGENTS.md`
- 当前启用的全局自动化：`development-lesson-review`
- 复盘变更日志：`{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-log.md`
- 复盘主游标：`{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-cursor.json`
- 自动化记忆：`{{CODEX_HOME}}/automations/development-lesson-review/memory.md`
- 持久记忆分层：
  - `skills/` 用于重复执行的工作流
  - `vault/` 用于持久状态和决策
  - `evals/` 用于失败案例和回归提示
  - `rules/` 用于权限和访问边界
  - `hooks/` 用于确定性校验逻辑

## Decisions

- 通用经验只有在跨项目适用时才写入全局层。
- 项目专属经验应保留在该项目自己的本地持久层。
- 后台复盘只提取简洁、可广泛复用的开发经验，避免沉淀一次性实现细节。
- 后台复盘用于观察 Codex 协作工作，包括近期对话/会话记录和工作区变化，而不只是仓库 diff。
- 每次后台复盘只要修改了持久指导文件，就应向 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-log.md` 追加一条简洁中文记录。
- 后台复盘不应重复总结已经存在于持久指导或复盘日志中的相同/近似经验。
- 后台复盘应使用 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-cursor.json` 作为主增量游标，区分已经复盘过的输入和新的对话、文件、仓库变化；`memory.md` 只作为人工可读运行记忆和最近结论。
- 后台复盘应默认保守写入：只有高置信度经验直接进入持久层；中置信度线索写入 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-candidates.md` 等待审查；低置信度线索只在本次总结中说明跳过原因。
- 后台复盘写入高频上下文文件前必须评估上下文成本；`AGENTS.md` 和 `SKILL.md` 只保留短规则和核心流程，历史、案例、审计和候选内容放入 `vault/` 或 references。
- 后台复盘写入 `skills/` 前必须先查找已有相关 skill；能迭代已有 skill 时优先更新已有 skill，只有没有合适承载点或新流程明显独立时才创建新 skill。
- 后台复盘不得持久化敏感信息；发现疑似 token、密钥、密码、cookie、授权头、私钥、连接串或用户隐私时，只在本次总结中说明未写入，不落日志、候选或规则。
- 长期项目每月应整理一次自动复盘材料：合并重复规则、清理或标记候选状态、归档旧日志、把稳定流程沉淀到 `skills/`，把可复现失败沉淀到 `evals/`。
- 自动复盘可以提出删除、降级或迁移建议，但不得在没有用户明确确认时自动删除或迁移既有长期规则。
- 删除、降级或迁移建议应写入 `{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-pending-changes.md` 等待人工确认。
- 月度维护应检查全局/项目规则、`skills/` 和 `hooks/` 之间是否存在重复、矛盾、覆盖关系错误或过期规则。
- 如果主游标 `lesson-review-cursor.json` 写入失败，后台复盘不应写入新的长期经验，避免重复扫描旧输入后重复沉淀。

## Open Items

- 观察到真实失败案例后，再补充具体 `evals/`。
- 当确定性检查足够清晰时，再补充可执行 `hooks/`。
- 为 `development-lesson-review` 增加独立月度压缩/归档自动化，或在每日复盘中检测月初时执行月度整理。
