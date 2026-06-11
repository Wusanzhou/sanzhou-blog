#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
MAINTENANCE_DIR="${LESSON_REVIEW_HOME:-}"
FIX="true"
DRY_RUN="false"

usage() {
  cat <<'EOF'
用法：
  ./scripts/check_permissions.sh [--codex-home /path/to/.codex] [--maintenance-dir /path/to/maintenance] [--no-fix] [--dry-run]

作用：
  检查自动经验总结所需维护目录和文件是否真的可写。
  默认会修复当前用户拥有的文件权限；不会使用 sudo，也不会绕过 macOS 系统授权。

参数：
  --codex-home P   Codex 配置目录，默认 $CODEX_HOME 或 ~/.codex。
  --maintenance-dir P
                  维护目录，默认 $LESSON_REVIEW_HOME；否则默认 $CODEX_HOME/automations/development-lesson-review/maintenance。
  --no-fix         只检查，不自动 chmod。
  --dry-run        只显示将检查和修复的内容，不实际写入。
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex-home)
      [[ $# -ge 2 ]] || { echo "缺少 --codex-home 参数值" >&2; exit 1; }
      CODEX_HOME_DIR="$2"
      shift 2
      ;;
    --maintenance-dir)
      [[ $# -ge 2 ]] || { echo "缺少 --maintenance-dir 参数值" >&2; exit 1; }
      MAINTENANCE_DIR="$2"
      shift 2
      ;;
    --no-fix)
      FIX="false"
      shift
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数：$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -n "$MAINTENANCE_DIR" ]]; then
  MAINT_DIR="$MAINTENANCE_DIR"
else
  MAINT_DIR="$CODEX_HOME_DIR/automations/development-lesson-review/maintenance"
fi
ARCHIVE_DIR="$MAINT_DIR/archive"
DASHBOARD="$MAINT_DIR/start_dashboard.py"
FILES=(
  "$MAINT_DIR/lesson-review-log.md"
  "$MAINT_DIR/lesson-review-candidates.md"
  "$MAINT_DIR/lesson-review-pending-changes.md"
  "$MAINT_DIR/lesson-review-cursor.json"
)

echo "权限检查目标：$MAINT_DIR"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] 将确保目录存在：$MAINT_DIR"
  echo "[dry-run] 将确保目录存在：$ARCHIVE_DIR"
  printf '[dry-run] 将检查文件：%s\n' "${FILES[@]}"
  echo "[dry-run] 未实际写入任何文件。"
  exit 0
fi

mkdir -p "$ARCHIVE_DIR"

if [[ "$FIX" == "true" ]]; then
  chmod u+rwx "$MAINT_DIR" "$ARCHIVE_DIR" 2>/dev/null || true
  for file in "${FILES[@]}"; do
    touch "$file"
    chmod u+rw "$file" 2>/dev/null || true
  done
  if [[ -f "$DASHBOARD" ]]; then
    chmod u+rwx "$DASHBOARD" 2>/dev/null || true
  fi
fi

failures=()

check_dir_write() {
  local dir="$1"
  local probe="$dir/.lesson-review-permission-test.$$"
  if ! printf 'permission probe\n' > "$probe" 2>/dev/null; then
    failures+=("目录不可写：$dir")
    return
  fi
  rm -f "$probe"
}

check_file_write() {
  local file="$1"
  local backup
  backup="$(mktemp)"
  if [[ -f "$file" ]]; then
    cp "$file" "$backup"
  else
    : > "$backup"
  fi
  if ! printf '\n' >> "$file" 2>/dev/null; then
    failures+=("文件不可写：$file")
    rm -f "$backup"
    return
  fi
  cp "$backup" "$file"
  rm -f "$backup"
}

check_dir_write "$MAINT_DIR"
check_dir_write "$ARCHIVE_DIR"
for file in "${FILES[@]}"; do
  check_file_write "$file"
done

if [[ ${#failures[@]} -gt 0 ]]; then
  echo "权限检查失败："
  printf '  - %s\n' "${failures[@]}"
  cat <<'EOF'

处理建议：
  1. 确认这些文件属于当前用户；如果不是，需要由拥有者或管理员修复属主。
  2. macOS 上到“系统设置 -> 隐私与安全性 -> 完全磁盘访问权限”，给 Codex、Terminal 或实际运行自动化的应用授权。
  3. 授权后重新运行安装脚本的 --upgrade，或重新运行 scripts/check_permissions.sh。
EOF
  exit 1
fi

echo "权限检查通过：维护目录、归档目录、日志、候选、待确认和 cursor 文件均可写。"
