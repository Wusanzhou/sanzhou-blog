# Development Lesson Review

这里放我整理过的 `Development Lesson Review` 定时复盘任务安装包。每个版本都是一个完整目录，彼此平级保存，不互相覆盖。

## 版本

```text
tools/development-lesson-review/
├── README.md
├── v1.0.0/
├── v1.0.0-20260611/
└── v1.0.1/
```

- `v1.0.0/`：最早迁入的 `1.0.0` 包，默认按 `UTC 10:00` 理解调度，对应北京时间 18:00。
- `v1.0.0-20260611/`：2026-06-11 迁入的 `1.0.0` 新构建，默认按本地时间 18:00 理解调度。
- `v1.0.1/`：2026-06-11 迁入的新版本，把长 prompt 拆成维护清单和规则手册。

以后如果还有新包，也直接放在这里，和旧版本平级。

## 怎么选

现在优先看 `v1.0.1/`，因为它在保留本地 18:00 调度说明的基础上，把复盘规则拆进了维护文件，安装脚本里的 prompt 更短。

保留旧目录是为了能回看历史包，不把旧版本直接覆盖掉。

## 安装

进入要安装的版本目录，再运行安装脚本：

```sh
cd tools/development-lesson-review/v1.0.1
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
