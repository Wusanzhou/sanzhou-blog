# Development Lesson Review v1.0.0

这是最早迁入仓库的 `Development Lesson Review` `1.0.0` 安装包。

这份包保持原样放在：

```text
tools/development-lesson-review/v1.0.0/
```

## 这版的调度说明

这版默认把执行时间写成 `UTC 10:00`，说明里按“UTC 10:00 对应北京时间 18:00”理解。

如果当前 Codex App 按本地时间解释 `BYHOUR`，更建议使用旁边的 `v1.0.0-20260611/`。

## 安装方式

```sh
./scripts/install.sh --repo /path/to/project --dry-run
./scripts/install.sh --repo /path/to/project
```

已有旧安装时：

```sh
./scripts/install.sh --repo /path/to/project --upgrade
```

完整参数见 [INSTALL.md](./INSTALL.md)。
