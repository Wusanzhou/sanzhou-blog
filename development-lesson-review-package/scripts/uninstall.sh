#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
REMOVE_VAULT="false"
DRY_RUN="false"

usage() {
  cat <<'EOF'
用法：
  ./scripts/uninstall.sh [--codex-home /path/to/.codex] [--remove-vault] [--dry-run]

参数：
  --codex-home P   Codex 配置目录，默认 $CODEX_HOME 或 ~/.codex。
  --remove-vault   同时删除本功能的维护目录。默认保留日志、主 memory 游标、cursor、候选和待确认变更。
  --dry-run        只预览将删除的文件，不实际删除。

默认行为只删除自动化目录：
  $CODEX_HOME/automations/development-lesson-review
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --codex-home)
      [[ $# -ge 2 ]] || { echo "缺少 --codex-home 参数值" >&2; exit 1; }
      CODEX_HOME_DIR="$2"
      shift 2
      ;;
    --remove-vault)
      REMOVE_VAULT="true"
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

delete_path() {
  local path="$1"
  if [[ -e "$path" ]]; then
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "[dry-run] 将删除：$path"
    else
      rm -rf "$path"
      echo "已删除：$path"
    fi
  else
    echo "不存在，跳过：$path"
  fi
}

echo "Codex Home: $CODEX_HOME_DIR"
echo "删除 vault 文件: $REMOVE_VAULT"
echo "dry-run: $DRY_RUN"

delete_path "$CODEX_HOME_DIR/automations/development-lesson-review"

if [[ "$REMOVE_VAULT" == "true" ]]; then
  delete_path "$CODEX_HOME_DIR/automations/development-lesson-review/maintenance"
fi

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] 未实际删除任何文件。"
else
  echo "卸载完成。"
fi
