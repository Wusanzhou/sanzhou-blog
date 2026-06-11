# Development Lesson Review

这里放我整理过的 `Development Lesson Review` 定时复盘任务安装包。每个版本都是一个完整目录，彼此平级保存，不互相覆盖。

## 版本

```text
tools/development-lesson-review/
├── README.md
├── v1.0.0/
└── v1.0.0-20260611/
```

- `v1.0.0/`：最早迁入的 `1.0.0` 包，默认按 `UTC 10:00` 理解调度，对应北京时间 18:00。
- `v1.0.0-20260611/`：2026-06-11 迁入的 `1.0.0` 新构建，默认按本地时间 18:00 理解调度。

源包里的 `VERSION` 都是 `1.0.0`，所以用目录名区分不同构建。以后如果还有新包，也直接放在这里，和旧版本平级。

## 怎么选

现在优先看 `v1.0.0-20260611/`，因为它修正了 Codex App 调度时间的说明：当前按本地时间解释 `BYHOUR`，默认本地 18:00。

保留 `v1.0.0/` 是为了能回看旧包，不把历史直接覆盖掉。

## 安装

进入要安装的版本目录，再运行安装脚本：

```sh
cd tools/development-lesson-review/v1.0.0-20260611
./scripts/install.sh --repo /path/to/project --dry-run
./scripts/install.sh --repo /path/to/project
```

已有旧安装时：

```sh
./scripts/install.sh --repo /path/to/project --upgrade
```

每个版本目录里的 `README.md` 和 `INSTALL.md` 记录了该版本自己的说明。

## 发布前检查

不要提交本机运行目录、真实 cursor、运行记忆、备份文件或密钥。基础检查：

```sh
find tools/development-lesson-review -name '*.bak.*' -print
rg -n "(OPENAI_API_KEY|GITHUB_TOKEN|BEGIN PRIVATE KEY|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._~+/=-]{20,})" tools/development-lesson-review
```
