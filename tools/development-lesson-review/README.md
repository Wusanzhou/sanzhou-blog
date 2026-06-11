# Development Lesson Review

`Development Lesson Review` 是一个给 Codex 用的定时复盘任务。它会定期看看最近的 Codex 会话和仓库变化，把以后还会用到的经验整理到本地文件里。

这个目录是发布用的干净安装包，不包含我本机的运行日志、备份文件、真实 cursor 或个人历史记录。

## 它会做什么

- 看最近的 Codex 会话和仓库改动。
- 找出反复出现的偏好、流程、验证遗漏和返工原因。
- 确定值得长期保留的内容后，写入 `AGENTS.md`、`skills/`、`vault/`、`evals/`、`rules/` 或 `hooks/`。
- 不够确定的内容先放进候选文件，等人工确认。
- 提供一个本地维护面板，用来查看日志、候选项、待确认变更、cursor 和运行记忆。

## 目录结构

```text
tools/development-lesson-review/
├── README.md
├── INSTALL.md
├── VERSION
├── scripts/
│   ├── install.sh
│   ├── uninstall.sh
│   ├── check_permissions.sh
│   └── start_dashboard.py
└── templates/
    ├── AGENTS.append.md
    ├── automations/development-lesson-review/
    │   ├── automation.toml.tmpl
    │   └── memory.md
    ├── hooks/validation.md
    ├── maintenance/
    │   ├── archive/README.md
    │   ├── lesson-review-candidates.md
    │   ├── lesson-review-cursor.json
    │   ├── lesson-review-log.md
    │   └── lesson-review-pending-changes.md
    └── vault/global-state.md
```

## 安装

先 dry-run 一次，看看它准备写哪些文件：

```sh
cd tools/development-lesson-review
./scripts/install.sh --repo /path/to/project --dry-run
```

确认没问题后再安装：

```sh
./scripts/install.sh --repo /path/to/project
```

要复盘多个仓库，就多传几次 `--repo`：

```sh
./scripts/install.sh \
  --repo /path/to/project-a \
  --repo /path/to/project-b
```

只想先装上、暂时不运行：

```sh
./scripts/install.sh --repo /path/to/project --paused
```

## 升级已有安装

本机已经装过旧版本时，用 `--upgrade`：

```sh
cd tools/development-lesson-review
./scripts/install.sh --repo /path/to/project --upgrade
```

升级会替换自动化配置、维护面板脚本、权限检查脚本，并补齐缺失模板。已有日志、cursor、运行记忆、候选项和待确认变更会保留；需要覆盖的关键文件会先备份成 `.bak.时间戳`。

## 默认安装位置

默认写到当前用户的 Codex Home：

```text
$CODEX_HOME/automations/development-lesson-review/
$CODEX_HOME/automations/development-lesson-review/maintenance/
$CODEX_HOME/vault/
$CODEX_HOME/hooks/
$CODEX_HOME/AGENTS.md
```

没有设置 `CODEX_HOME` 时，通常就是：

```text
$HOME/.codex
```

一般不用改维护目录。默认目录和自动化放在一起，后面排查也简单。

## 维护面板

安装后可以打开本地维护面板：

```sh
python3 "$HOME/.codex/automations/development-lesson-review/maintenance/start_dashboard.py"
```

如果设置了 `CODEX_HOME`：

```sh
python3 "$CODEX_HOME/automations/development-lesson-review/maintenance/start_dashboard.py"
```

面板里可以看复盘日志、候选项、待确认变更、cursor、运行记忆和归档说明。

## 发布注意事项

发到 GitHub 前，确认只提交这个安装包目录里的文件。下面这些不要提交：

- `$HOME/.codex/automations/development-lesson-review/` 里的真实运行目录。
- `*.bak.*` 备份文件。
- 真实 `lesson-review-cursor.json`。
- 真实 `memory.md` 运行记忆。
- 任何包含 token、密钥、cookie、授权头、连接串或用户隐私的内容。

发布前可以跑一遍：

```sh
find tools/development-lesson-review -name '*.bak.*' -print
rg -n "(OPENAI_API_KEY|GITHUB_TOKEN|BEGIN PRIVATE KEY|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._~+/=-]{20,})" tools/development-lesson-review
bash -n tools/development-lesson-review/scripts/install.sh
bash -n tools/development-lesson-review/scripts/uninstall.sh
bash -n tools/development-lesson-review/scripts/check_permissions.sh
python3 -m py_compile tools/development-lesson-review/scripts/start_dashboard.py
```

如果 `rg` 只命中了安全说明里的示例词，不一定是泄露；看一眼命中的内容再判断。

## 更多说明

更多安装参数、cursor 规则和权限检查细节见 [INSTALL.md](./INSTALL.md)。
