# Development Lesson Review v1.0.0-20260611

这是 `Development Lesson Review` 的 `1.0.0` 版本在 2026-06-11 迁入的完整包。

这份包没有覆盖旧版本，而是和旧版本平级放在：

```text
tools/development-lesson-review/v1.0.0-20260611/
```

## 这版主要变化

- 默认调度从 `UTC 10:00` 改为本地时间 `18:00`。
- 安装脚本里的 `--utc-hour` 说明改为按本地小时解释。
- `INSTALL.md` 同步说明：当前 Codex App 按本地时间解释 `BYHOUR`。

源包里的 `VERSION` 仍然是 `1.0.0`，所以这里用目录名 `v1.0.0-20260611` 区分这次迁入的构建。

## 安装方式

如果要安装这一版，进入当前目录运行：

```sh
./scripts/install.sh --repo /path/to/project --dry-run
./scripts/install.sh --repo /path/to/project
```

如果已经安装过旧版：

```sh
./scripts/install.sh --repo /path/to/project --upgrade
```

## 发布检查

迁入时已排除源目录里的 `*.bak.*` 文件。发布前仍建议检查一次：

```sh
find tools/development-lesson-review/v1.0.0-20260611 -name '*.bak.*' -print
bash -n tools/development-lesson-review/v1.0.0-20260611/scripts/install.sh
bash -n tools/development-lesson-review/v1.0.0-20260611/scripts/uninstall.sh
bash -n tools/development-lesson-review/v1.0.0-20260611/scripts/check_permissions.sh
python3 -m py_compile tools/development-lesson-review/v1.0.0-20260611/scripts/start_dashboard.py
```
