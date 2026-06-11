# Development Lesson Review 安装说明

这个包用于给 Codex 安装一个“自动经验总结”功能。安装后，Codex 会定期复盘近期协作记录和仓库变化，把可复用经验写入合适的持久层，并用中文记录本次做了什么。

当前版本：`1.0.0`

## 快速摘要

- 作用：把长期有用的 Codex 协作经验沉淀到本地持久层。
- 默认时间：每天本地时间 18:00；当前 Codex App 按本地时间解释调度小时。
- 安全策略：高置信度才直接写入，中置信度进候选，疑似敏感内容不落盘。
- 游标策略：`maintenance/lesson-review-cursor.json` 是稳定机器游标；`memory.md` 是人工可读运行记忆。
- 权限策略：维护目录默认放在 `$CODEX_HOME/automations/development-lesson-review/maintenance`，与自动化同属一个稳定可写范围。
- 工作区策略：自动化工作区包含 Codex Home 和目标仓库；维护文件位于 Codex Home 内。
- 审查策略：所有人工维护文件集中在维护目录中，安装包不携带发送方历史记录。
- 建议安装：先运行 `--dry-run`，确认修改范围后再正式安装；不想立即启用时加 `--paused`。

## 安装方式

把整个压缩包交给本地 Codex 后，让 Codex 在解压目录运行：

```sh
./scripts/install.sh --repo /path/to/project
```

如果要监听多个仓库，可以重复传入：

```sh
./scripts/install.sh --repo /path/to/project-a --repo /path/to/project-b
```

默认会创建启用状态的自动化，调度为每天本地时间 18:00。当前 Codex App 按本地时间解释 `BYHOUR`，配置会写成 `BYHOUR=18`。

如果想先暂停安装：

```sh
./scripts/install.sh --repo /path/to/project --paused
```

如果本机已经安装过旧版本，可以使用升级模式。升级模式会更新自动化配置、维护面板脚本、权限检查脚本和缺失模板，但不会重置既有复盘日志、稳定 cursor、运行记忆、候选经验和待确认变更；关键文件覆盖前会先生成 `.bak.时间戳` 备份：

```sh
./scripts/install.sh --repo /path/to/project --upgrade
```

如果只想预览会改哪些文件，不实际写入，可以使用 dry-run：

```sh
./scripts/install.sh --repo /path/to/project --dry-run
```

如果确实要自定义维护目录，可以传入：

```sh
./scripts/install.sh --repo /path/to/project --maintenance-dir /path/to/maintenance
```

默认不建议自定义维护目录。最稳定的结构是让维护目录留在：

```text
$CODEX_HOME/automations/development-lesson-review/maintenance
```

## 权限检查

安装脚本会在安装完成前检查这些文件是否可写：

```text
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-log.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-candidates.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-pending-changes.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-cursor.json
```

检查方式不是只看权限数字，而是实际创建临时文件、追加临时内容、再恢复原文件内容。这样可以发现自动总结真正运行时会遇到的写入问题。

如果这些文件属于当前用户，安装脚本会自动执行本用户范围内的权限修复，例如补上目录进入权限、文件读写权限和面板脚本执行权限。它不会使用 `sudo`，也不会绕过 macOS 系统授权。

## 游标策略

当前版本使用两个互补文件：

```text
$CODEX_HOME/automations/development-lesson-review/memory.md
$CODEX_HOME/automations/development-lesson-review/maintenance/lesson-review-cursor.json
```

`lesson-review-cursor.json` 是主增量游标，用来记录上次复盘处理到哪里、哪些文件和仓库状态已经检查过。它更适合做增量扫描和稳定查重。

`memory.md` 是人工可读摘要和运行记忆，用来记录本轮复盘检查了什么、跳过了什么、是否发现新经验、是否有权限问题。它辅助审查，但不承担主游标职责。

每轮复盘结束后，自动化先把新的增量进度写入 `lesson-review-cursor.json`，写入时先生成临时 JSON、校验可解析后再替换目标文件。cursor 写入成功后，再更新 `memory.md` 作为中文运行摘要。如果 cursor 写入失败，不应写入新的长期经验，避免重复扫描旧输入后重复沉淀。

## 维护面板

安装后可启动本地维护面板：

```sh
python3 "$CODEX_HOME/automations/development-lesson-review/maintenance/start_dashboard.py"
```

如果没有设置 `CODEX_HOME`，默认路径通常是：

```sh
python3 "$HOME/.codex/automations/development-lesson-review/maintenance/start_dashboard.py"
```

打开后可以在本地网页中集中查看和编辑复盘日志、候选经验、待确认变更、复盘游标、自动化记忆和归档说明。页面使用顶部横向导航，复盘日志会按每次记录拆成卡片，候选经验和待确认变更可以按状态快速筛选并通过按钮处理，自动化记忆会按时间点拆分，复盘游标以一个完整 JSON 模块展示。面板还提供搜索、最近 7 天/30 天/本月/上月筛选、安装自检、备份查看和恢复、候选与旧日志归档、规则冲突检查。复盘游标是机器状态入口，自动化记忆是人工审查入口。

如果希望改成其他本地执行时间，可以显式传入小时：

```sh
./scripts/install.sh --repo /path/to/project --utc-hour 18
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

安装前后可以让 Codex 检查这些点：

- 自动化 prompt 是否为中文正文。
- `cwds` 是否是自己的仓库路径。
- `rrule` 是否对应期望执行时间。
- 已有 `$CODEX_HOME/AGENTS.md`、`hooks/validation.md`、`vault/global-state.md` 是否被备份。
- `memory.md` 是否是干净初始记忆，不包含发送方历史数据。
- `lesson-review-cursor.json` 是否是干净初始 cursor，不包含发送方仓库状态。
- 维护面板是否默认打开 `$CODEX_HOME/automations/development-lesson-review/maintenance`。
- 降噪规则是否符合预期：高置信度经验直接写入，中置信度只进候选文件，低置信度只在运行总结里说明跳过。
- 上下文预算规则是否符合预期：`AGENTS.md` 和 `SKILL.md` 只保留短规则和核心流程，历史、案例、审计和候选内容放入 `vault/` 或 references。
- 长期维护规则是否符合预期：候选有状态、作用范围、复查时间；旧日志和旧候选按月份归档。
- 敏感信息保护是否符合预期：疑似 token、密钥、密码、cookie、授权头、私钥、连接串或用户隐私不写入任何持久文件。
- 安装前是否通过 dry-run 预览修改范围，并通过写权限预检。
