# 自动经验总结执行清单

本文件是 `development-lesson-review` 每次运行时优先读取的短清单，用来保证执行顺序稳定。详细判断标准见同目录的 `review-playbook.md`。

## 每轮启动

- 视为无聊天历史状态，不依赖上一轮 chat 或上一轮自动化线程。
- 读取主游标：`{{CODEX_HOME}}/automations/development-lesson-review/maintenance/lesson-review-cursor.json`。
- 读取运行记忆：`{{CODEX_HOME}}/automations/development-lesson-review/memory.md`。
- 检查本轮环境权限说明，记录是否可见 `sandbox_mode`、`permission_profile`、`writable_roots` 或 `danger-full-access`；如果结构化字段不可见，说明本轮上下文未暴露，并以实际写入结果判断。
- 只处理主游标之后的新输入：会话/对话元数据变化、仓库 head 变化、工作区状态哈希变化、维护文件变化。

## 每轮复盘

- 复盘重点是协作方式：重复偏好、重复工作流、遗漏假设、澄清循环、验证缺口、权限边界、失败模式。
- 默认保守写入：宁可漏掉弱经验，也不要把噪声写进长期记忆。
- `development-lesson-review` 自身产生的常规维护线程按维护噪声处理，除非包含新的持久指导决策。
- 读取会话记录时先做结构化增量检查，避免大段读取或落盘疑似敏感正文。

## 写入判断

- 涉及直接写入、候选、待确认、冲突处理、删除/迁移/降级、细粒度 `AGENTS.md` 或月度整理时，先读取 `review-playbook.md` 对应章节。
- 高置信度经验才直接写入最窄持久层。
- 中置信度线索写入 `lesson-review-candidates.md`。
- 删除、降级、迁移或修改既有长期内容的建议写入 `lesson-review-pending-changes.md`。
- 低置信度、一次性、范围过宽、证据不足或重复内容不写入，只在本次总结中说明跳过原因。

## 写入顺序

- 写任何长期经验前，先确认主游标可写；如果主游标不可写，不写入新的长期经验。
- 写主游标时先写临时 JSON，解析通过后再替换目标文件。
- 主游标写入成功后，再更新 `memory.md` 作为中文运行摘要。
- 只要修改了持久指导文件，就向 `lesson-review-log.md` 追加一条简洁中文记录。
- 如果只写候选或待确认，也要在本次回复中说明条目和暂不直接执行原因。

## 每轮收尾

- 最终中文回复必须说明检查范围、写入文件、候选/待确认条目、跳过内容、规则冲突、权限或写入失败、cursor 和 memory 写入结果。
- 只要写入或修改了任何文件，必须包含简洁但到位的“变更清单”。
- 没有文件变更时，也要明确说明“本轮没有写入或修改持久文件”。
