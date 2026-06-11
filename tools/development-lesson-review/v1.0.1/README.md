# Development Lesson Review v1.0.1

这是 2026-06-11 迁入的 `Development Lesson Review` `1.0.1` 完整安装包。

这份包和旧版本平级保存：

```text
tools/development-lesson-review/v1.0.1/
```

## 这版主要变化

- `VERSION` 更新为 `1.0.1`。
- 安装脚本里的复盘 prompt 明显压缩，把详细规则拆到维护文件里。
- 新增维护模板：
  - `templates/maintenance/review-checklist.md`
  - `templates/maintenance/review-playbook.md`
- 维护面板脚本有更新。

注意：源包里的 `INSTALL.md` 仍写着“当前版本：`1.0.0`”。这里按 `VERSION` 文件认定为 `1.0.1`，暂不改源包内容。

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

## 发布检查

迁入时已排除 `*.bak.*` 文件。发布前可以再跑一次：

```sh
find tools/development-lesson-review/v1.0.1 -name '*.bak.*' -print
bash -n tools/development-lesson-review/v1.0.1/scripts/install.sh
bash -n tools/development-lesson-review/v1.0.1/scripts/uninstall.sh
bash -n tools/development-lesson-review/v1.0.1/scripts/check_permissions.sh
python3 -m py_compile tools/development-lesson-review/v1.0.1/scripts/start_dashboard.py
```
