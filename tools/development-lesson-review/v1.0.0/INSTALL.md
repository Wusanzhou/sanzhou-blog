# Development Lesson Review 安装说明

这个包用来给 Codex 安装一个定时复盘任务。安装后，它会定期检查近期 Codex 会话和仓库变化，把以后还会用到的经验写到合适的本地文件里，并用中文留下运行记录。

当前版本：`1.0.0`

## 快速摘要

- 作用：整理长期有用的 Codex 协作经验。
- 默认时间：每天 UTC 10:00；如果调度器按 UTC 解释，对应北京时间 18:00。
- 安全策略：高置信度才直接写入，中置信度进候选，疑似敏感内容不落盘。
- Cursor：`maintenance/lesson-review-cursor.json` 记录机器进度；`memory.md` 方便人看最近运行情况。
- 维护目录：默认放在 `$CODEX_HOME/automations/development-lesson-review/maintenance`。
- 工作区：自动化会读取 Codex Home 和你传入的目标仓库。
- 发布包：不包含发送方的历史记录、本机日志或真实运行状态。
- 建议：先跑 `--dry-run`，确认修改范围后再正式安装；不想立即启用就加 `--paused`。

## 安装方式

在解压目录运行：

```sh
./scripts/install.sh --repo /path/to/project
```

要复盘多个仓库，可以重复传入：

```sh
./scripts/install.sh --repo /path/to/project-a --repo /path/to/project-b
```

默认安装后立即启用，时间是每天北京时间 18:00。当前 Codex 调度器按 UTC 小时解释时，配置会写成 `BYHOUR=10`。

如果想先安装但暂时不运行：

```sh
./scripts/install.sh --repo /path/to/project --paused
```

如果本机已经安装过旧版本，使用升级模式。升级会更新自动化配置、维护面板脚本、权限检查脚本和缺失模板，但不会重置已有日志、cursor、运行记忆、候选项和待确认变更；关键文件覆盖前会先生成 `.bak.时间戳` 备份：

```sh
./scripts/install.sh --repo /path/to/project --upgrade
```

只想预览修改范围、不实际写入：

```sh
./scripts/install.sh --repo /path/to/project --dry-run
```

确实需要自定义维护目录时：

```sh
./scripts/install.sh --repo /path/to/project --maintenance-dir /path/to/maintenance
```

一般不建议自定义维护目录。最省心的结构是：

```text
$CODEX_HOME/automations/development-lesson-review/maintenance
```

## 权限检查

安装脚本会在结束前检查这些文件能不能写：

```text
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-log.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-candidates.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-pending-changes.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-cursor.json
```

检查时不会只看权限数字，而是实际创建临时文件、追加临时内容，再恢复原文件内容。这样能发现真实运行时可能遇到的写入问题。

如果这些文件属于当前用户，脚本会在用户权限范围内做修复，比如补上目录进入权限、文件读写权限和面板脚本执行权限。它不会使用 `sudo`，也不会绕过 macOS 系统授权。

## 游标策略

当前版本主要看两个文件：

```text
$CODEX_HOME/automations/development-lesson-review/memory.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-cursor.json
```

`lesson-review-cursor.json` 是主 cursor，用来记录上次复盘处理到哪里、哪些文件和仓库状态已经检查过。

`memory.md` 是给人看的运行摘要，记录本轮检查了什么、跳过了什么、是否发现新经验、是否有权限问题。它只辅助审查，不承担主 cursor 职责。

每轮复盘结束后，任务会先把新进度写入 `lesson-review-cursor.json`。写入时先生成临时 JSON，确认能解析后再替换目标文件。cursor 写入成功后，再更新 `memory.md`。如果 cursor 写入失败，就不写新的长期经验，避免下次重复扫描旧内容。

## 维护面板

安装后可以启动本地维护面板：

```sh
python3 "$CODEX_HOME/automations/development-lesson-review/maintenance/start_dashboard.py"
```

如果没有设置 `CODEX_HOME`，默认路径通常是：

```sh
python3 "$HOME/.codex/automations/development-lesson-review/maintenance/start_dashboard.py"
```

打开后可以查看和编辑复盘日志、候选项、待确认变更、cursor、运行记忆和归档说明。面板支持搜索、按时间筛选、安装自检、备份查看和恢复、候选与旧日志归档、规则冲突检查。cursor 主要给机器续跑用，运行记忆主要给人审查用。

如果本地时区或调度器行为不同，可以手动指定 UTC 小时：

```sh
./scripts/install.sh --repo /path/to/project --utc-hour 10
```

## 安装内容

- 自动化：`$CODEX_HOME/automations/development-lesson-review/automation.toml`
- 自动化记忆：`$CODEX_HOME/automations/development-lesson-review/memory.md`
- 维护目录：`$CODEX_HOME/automations/development-lesson-review/maintenance/`
- 复盘日志：`$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-log.md`
- 复盘候选：`$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-candidates.md`
- 待确认变更：`$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-pending-changes.md`
- canonical cursor：`$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-cursor.json`
- 复盘归档目录：`$CODEX_HOME/automations/development-lesson-review/maintenance/archive/`
- 本地维护面板：`$CODEX_HOME/automations/development-lesson-review/maintenance/start_dashboard.py`
- 权限检查脚本：`$CODEX_HOME/automations/development-lesson-review/maintenance/check_permissions.sh`
- 安装后自检报告：`$CODEX_HOME/automations/development-lesson-review/maintenance/install-self-check.md`
- 全局状态：`$CODEX_HOME/vault/global-state.md`
- 校验说明：`$CODEX_HOME/hooks/validation.md`
- 全局指导：向 `$CODEX_HOME/AGENTS.md` 追加必要段落

## 审查重点

安装前后建议检查这些点：

- 自动化 prompt 是否主要用中文书写。
- `cwds` 是否是自己的仓库路径。
- `rrule` 是否对应期望执行时间。
- 已有 `$CODEX_HOME/AGENTS.md`、`hooks/validation.md`、`vault/global-state.md` 是否被备份。
- `memory.md` 是否是干净初始内容，不包含发送方历史数据。
- `lesson-review-cursor.json` 是否是干净初始 cursor，不包含发送方仓库状态。
- 维护面板是否默认打开 `$CODEX_HOME/automations/development-lesson-review/maintenance`。
- 降噪规则是否符合预期：高置信度直接写入，中置信度进候选，低置信度只在运行总结里说明跳过。
- 上下文成本是否可控：`AGENTS.md` 和 `SKILL.md` 只放短规则和核心流程，历史、案例、审计和候选内容放到 `vault/` 或 references。
- 长期维护规则是否符合预期：候选有状态、作用范围、复查时间；旧日志和旧候选按月份归档。
- 敏感信息保护是否符合预期：疑似 token、密钥、密码、cookie、授权头、私钥、连接串或用户隐私不写入任何持久文件。
- 安装前是否通过 dry-run 预览修改范围，并通过写权限预检。
