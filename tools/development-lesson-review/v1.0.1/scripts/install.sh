#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$PACKAGE_DIR/templates"

CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
MAINTENANCE_DIR="${LESSON_REVIEW_HOME:-}"
UTC_HOUR="18"
STATUS="ACTIVE"
MODEL="gpt-5.5"
UPGRADE="false"
DRY_RUN="false"
REPOS=()
PACKAGE_VERSION="$(tr -d '[:space:]' < "$PACKAGE_DIR/VERSION")"

usage() {
  cat <<'EOF'
用法：
  ./scripts/install.sh --repo /path/to/project [--repo /path/to/another] [--paused] [--upgrade] [--dry-run] [--utc-hour 18] [--model gpt-5.5] [--maintenance-dir /path/to/maintenance]

参数：
  --repo PATH      要让自动总结观察的仓库或工作目录，可传多次。
  --paused         安装后先暂停自动化。
  --upgrade        升级已有安装，不重置日志、游标和候选经验。
  --dry-run        只预览将创建、修改、备份的文件，不实际写入。
  --utc-hour H     写入调度器的本地小时。当前 Codex App 按本地时间解释 BYHOUR，北京时间 18:00 对应 18。
  --model NAME     自动化使用的模型，默认 gpt-5.5。
  --codex-home P   Codex 配置目录，默认 $CODEX_HOME 或 ~/.codex。
  --maintenance-dir P
                  维护目录，默认 $LESSON_REVIEW_HOME；
                  否则默认 $CODEX_HOME/automations/development-lesson-review/maintenance。
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "缺少 --repo 参数值" >&2; exit 1; }
      REPOS+=("$2")
      shift 2
      ;;
    --paused)
      STATUS="PAUSED"
      shift
      ;;
    --upgrade)
      UPGRADE="true"
      shift
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --utc-hour)
      [[ $# -ge 2 ]] || { echo "缺少 --utc-hour 参数值" >&2; exit 1; }
      UTC_HOUR="$2"
      shift 2
      ;;
    --model)
      [[ $# -ge 2 ]] || { echo "缺少 --model 参数值" >&2; exit 1; }
      MODEL="$2"
      shift 2
      ;;
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

if [[ ${#REPOS[@]} -eq 0 ]]; then
  echo "至少需要传入一个 --repo 路径。" >&2
  usage >&2
  exit 1
fi

for repo in "${REPOS[@]}"; do
  if [[ ! -d "$repo" ]]; then
    echo "仓库路径不存在：$repo" >&2
    exit 1
  fi
done

if ! [[ "$UTC_HOUR" =~ ^[0-9]+$ ]] || (( UTC_HOUR < 0 || UTC_HOUR > 23 )); then
  echo "--utc-hour 必须是 0 到 23 的整数。" >&2
  exit 1
fi

if [[ -z "$MAINTENANCE_DIR" ]]; then
  MAINTENANCE_DIR="$CODEX_HOME_DIR/automations/development-lesson-review/maintenance"
fi

backup_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    local backup="${path}.bak.$(date +%Y%m%d%H%M%S)"
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "[dry-run] 将备份：$path -> $backup"
      return
    fi
    cp "$path" "$backup"
    echo "已备份：$path -> $backup"
  fi
}

ensure_writable_dir() {
  local dir="$1"
  local parent
  if [[ -d "$dir" ]]; then
    parent="$dir"
  else
    parent="$(dirname "$dir")"
    while [[ ! -d "$parent" && "$parent" != "/" ]]; do
      parent="$(dirname "$parent")"
    done
  fi
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "[dry-run] 检查可写目录：$dir"
    return
  fi
  if [[ ! -w "$parent" ]]; then
    echo "目录不可写：$parent" >&2
    exit 1
  fi
}

render_template() {
  local src="$1"
  local dst="$2"
  python3 - "$src" "$dst" "$CODEX_HOME_DIR" "$TODAY" "$NOW" "$NOW_MS" "$UTC_HOUR" "$STATUS" "$MODEL" "$CWDS_JSON" "$PROMPT" <<'PY'
import sys
from pathlib import Path

src, dst, codex_home, today, now, now_ms, utc_hour, status, model, cwds_json, prompt = sys.argv[1:]
text = Path(src).read_text()
replacements = {
    "{{CODEX_HOME}}": codex_home,
    "{{DATE}}": today,
    "{{NOW}}": now,
    "{{NOW_MS}}": now_ms,
    "{{UTC_HOUR}}": utc_hour,
    "{{STATUS}}": status,
    "{{MODEL}}": model,
    "{{CWDS_JSON}}": cwds_json,
    "{{PROMPT}}": prompt.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n"),
}
for key, value in replacements.items():
    text = text.replace(key, value)
Path(dst).parent.mkdir(parents=True, exist_ok=True)
Path(dst).write_text(text)
PY
}

render_to_temp() {
  local src="$1"
  local tmp
  tmp="$(mktemp)"
  render_template "$src" "$tmp"
  printf '%s\n' "$tmp"
}

json_array() {
  python3 - "$@" <<'PY'
import json
import sys
print(json.dumps(sys.argv[1:], ensure_ascii=False))
PY
}

TODAY="$(date '+%Y-%m-%d %H:%M')"
if date -Iseconds >/dev/null 2>&1; then
  NOW="$(date -Iseconds)"
else
  NOW="$(date '+%Y-%m-%dT%H:%M:%S%z')"
fi
NOW_MS="$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)"
CWDS_JSON="$(json_array "$CODEX_HOME_DIR" "${REPOS[@]}")"

PROMPT="$(cat <<EOF
你是 `development-lesson-review` 自动复盘任务，用于复盘近期 Codex 协作工作，包括 `$CODEX_HOME_DIR` 下可用的近期对话/会话记录，以及相关工作区变化。每次运行都视为无聊天历史状态，不依赖上一轮 chat 或上一轮自动化线程。

开始时必须读取执行清单 `$MAINTENANCE_DIR/review-checklist.md`。涉及写入判断、候选、待确认、冲突处理、删除/迁移/降级、细粒度 `AGENTS.md`、月度整理或上下文成本判断时，必须读取规则手册 `$MAINTENANCE_DIR/review-playbook.md` 对应章节；如果这些规则文件缺失或不可读，停止写入新的长期经验并在本次中文总结中报告。

主游标是 `$MAINTENANCE_DIR/lesson-review-cursor.json`；`$CODEX_HOME_DIR/automations/development-lesson-review/memory.md` 只作为人工可读运行记忆和最近结论。维护目录保存复盘日志、候选经验、待确认变更、主游标、规则文档和归档内容。

每轮只处理主游标之后的新输入：会话/对话元数据变化、仓库 head 变化、工作区状态哈希变化和维护文件变化。`development-lesson-review` 自身产生的常规维护线程按维护噪声处理，除非其中包含新的持久指导决策。

默认保守写入：高置信度经验才直接写入最窄持久层；中置信度线索写入候选经验；删除、降级、迁移或修改既有长期内容的建议写入待确认变更；低置信度、一次性、范围过宽、证据不足、重复或疑似敏感内容不写入。不得持久化 token、密钥、密码、cookie、授权头、私钥、证书、完整连接串、完整内部接口参数或用户隐私数据。

写任何长期经验前，先确认主游标可写；如果主游标不可写，不写入新的长期经验。写主游标时先写临时 JSON，解析通过后再替换目标文件。主游标写入成功后，再更新 `memory.md` 中文运行摘要。只要修改了持久指导文件，就向维护日志追加简洁中文记录。

自动总结和持久指导更新正文使用中文。每次运行结束时，用中文说明检查范围、写入文件、候选/待确认条目、跳过原因、规则冲突、权限或写入失败、cursor 和 memory 写入结果。只要写入或修改了任何文件，最终回复必须包含简洁但到位的“变更清单”；没有文件变更时，也要明确说明“本轮没有写入或修改持久文件”。
EOF
)"

TARGET_DIRS=(
  "$CODEX_HOME_DIR"
  "$MAINTENANCE_DIR"
  "$CODEX_HOME_DIR/automations/development-lesson-review"
  "$CODEX_HOME_DIR/vault"
  "$MAINTENANCE_DIR/archive"
  "$CODEX_HOME_DIR/hooks"
  "$CODEX_HOME_DIR/skills"
  "$CODEX_HOME_DIR/evals"
  "$CODEX_HOME_DIR/rules"
)

TARGET_FILES=(
  "$CODEX_HOME_DIR/automations/development-lesson-review/automation.toml"
  "$CODEX_HOME_DIR/automations/development-lesson-review/memory.md"
  "$MAINTENANCE_DIR/lesson-review-log.md"
  "$MAINTENANCE_DIR/lesson-review-candidates.md"
  "$MAINTENANCE_DIR/lesson-review-pending-changes.md"
  "$MAINTENANCE_DIR/lesson-review-cursor.json"
  "$MAINTENANCE_DIR/archive/README.md"
  "$MAINTENANCE_DIR/start_dashboard.py"
  "$MAINTENANCE_DIR/check_permissions.sh"
  "$MAINTENANCE_DIR/install-self-check.md"
  "$CODEX_HOME_DIR/vault/global-state.md"
  "$CODEX_HOME_DIR/hooks/validation.md"
  "$CODEX_HOME_DIR/AGENTS.md"
)

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[dry-run] 版本: $PACKAGE_VERSION"
  echo "[dry-run] Codex Home: $CODEX_HOME_DIR"
  echo "[dry-run] 集中维护目录: $MAINTENANCE_DIR"
  echo "[dry-run] 状态: $STATUS"
  echo "[dry-run] 升级模式: $UPGRADE"
  echo "[dry-run] 调度: 本地 ${UTC_HOUR}:00"
  echo "[dry-run] 仓库: ${REPOS[*]}"
  echo "[dry-run] 自动化工作区会包含 Codex Home 和仓库路径；维护目录位于 Codex Home 内。"
  echo "[dry-run] 将确保目录存在:"
  printf '  %s\n' "${TARGET_DIRS[@]}"
  echo "[dry-run] 将创建或更新文件:"
  printf '  %s\n' "${TARGET_FILES[@]}"
  for path in "${TARGET_FILES[@]}"; do
    backup_file "$path"
  done
  for dir in "${TARGET_DIRS[@]}"; do
    ensure_writable_dir "$dir"
  done
  echo "[dry-run] 未实际写入任何文件。"
  exit 0
fi

for dir in "${TARGET_DIRS[@]}"; do
  ensure_writable_dir "$dir"
done

mkdir -p \
  "$CODEX_HOME_DIR/automations/development-lesson-review" \
  "$CODEX_HOME_DIR/vault" \
  "$MAINTENANCE_DIR/archive" \
  "$CODEX_HOME_DIR/hooks" \
  "$CODEX_HOME_DIR/skills" \
  "$CODEX_HOME_DIR/evals" \
  "$CODEX_HOME_DIR/rules"

backup_file "$CODEX_HOME_DIR/automations/development-lesson-review/automation.toml"
backup_file "$CODEX_HOME_DIR/automations/development-lesson-review/memory.md"
backup_file "$MAINTENANCE_DIR/lesson-review-log.md"
backup_file "$MAINTENANCE_DIR/lesson-review-candidates.md"
backup_file "$MAINTENANCE_DIR/lesson-review-pending-changes.md"
backup_file "$MAINTENANCE_DIR/lesson-review-cursor.json"
backup_file "$CODEX_HOME_DIR/vault/global-state.md"
backup_file "$CODEX_HOME_DIR/hooks/validation.md"
backup_file "$CODEX_HOME_DIR/AGENTS.md"

render_template "$TEMPLATE_DIR/automations/development-lesson-review/automation.toml.tmpl" "$CODEX_HOME_DIR/automations/development-lesson-review/automation.toml"

if [[ "$UPGRADE" != "true" || ! -f "$CODEX_HOME_DIR/automations/development-lesson-review/memory.md" ]]; then
  render_template "$TEMPLATE_DIR/automations/development-lesson-review/memory.md" "$CODEX_HOME_DIR/automations/development-lesson-review/memory.md"
fi

if [[ "$UPGRADE" == "true" && -f "$MAINTENANCE_DIR/lesson-review-log.md" ]]; then
  {
    printf '\n### %s - 升级自动经验总结安装包\n\n' "$TODAY"
    printf -- '- 来源：运行安装包升级模式。\n'
    printf -- '- 变更文件：`%s/automations/development-lesson-review/automation.toml` 以及缺失的模板规则文件。\n' "$CODEX_HOME_DIR"
    printf -- '- 经验：升级模式应保留既有复盘日志、稳定 cursor、运行记忆和候选经验，只更新自动化 prompt 和缺失规则。\n'
    printf -- '- 分层理由：升级记录放入复盘日志，避免静默改变自动化行为。\n'
    printf -- '- 校验：安装脚本未重置既有 `memory.md`、`lesson-review-cursor.json` 或 `lesson-review-candidates.md`。\n'
  } >> "$MAINTENANCE_DIR/lesson-review-log.md"
else
  render_template "$TEMPLATE_DIR/maintenance/lesson-review-log.md" "$MAINTENANCE_DIR/lesson-review-log.md"
fi

if [[ ! -f "$MAINTENANCE_DIR/lesson-review-candidates.md" ]]; then
  render_template "$TEMPLATE_DIR/maintenance/lesson-review-candidates.md" "$MAINTENANCE_DIR/lesson-review-candidates.md"
fi

if [[ ! -f "$MAINTENANCE_DIR/lesson-review-pending-changes.md" ]]; then
  render_template "$TEMPLATE_DIR/maintenance/lesson-review-pending-changes.md" "$MAINTENANCE_DIR/lesson-review-pending-changes.md"
fi

if [[ ! -f "$MAINTENANCE_DIR/lesson-review-cursor.json" ]]; then
  render_template "$TEMPLATE_DIR/maintenance/lesson-review-cursor.json" "$MAINTENANCE_DIR/lesson-review-cursor.json"
fi

render_template "$TEMPLATE_DIR/maintenance/archive/README.md" "$MAINTENANCE_DIR/archive/README.md"
cp "$PACKAGE_DIR/scripts/start_dashboard.py" "$MAINTENANCE_DIR/start_dashboard.py"
chmod +x "$MAINTENANCE_DIR/start_dashboard.py"
cp "$PACKAGE_DIR/scripts/check_permissions.sh" "$MAINTENANCE_DIR/check_permissions.sh"
chmod +x "$MAINTENANCE_DIR/check_permissions.sh"
if [[ -f "$CODEX_HOME_DIR/vault/global-state.md" ]]; then
  if ! grep -q "development-lesson-review" "$CODEX_HOME_DIR/vault/global-state.md"; then
    tmp="$(render_to_temp "$TEMPLATE_DIR/vault/global-state.md")"
    {
      printf '\n'
      cat "$tmp"
    } >> "$CODEX_HOME_DIR/vault/global-state.md"
    rm -f "$tmp"
  fi
else
  render_template "$TEMPLATE_DIR/vault/global-state.md" "$CODEX_HOME_DIR/vault/global-state.md"
fi

if [[ -f "$CODEX_HOME_DIR/hooks/validation.md" ]]; then
  if ! grep -q "Background Review Check" "$CODEX_HOME_DIR/hooks/validation.md"; then
    tmp="$(render_to_temp "$TEMPLATE_DIR/hooks/validation.md")"
    {
      printf '\n'
      cat "$tmp"
    } >> "$CODEX_HOME_DIR/hooks/validation.md"
    rm -f "$tmp"
  fi
else
  render_template "$TEMPLATE_DIR/hooks/validation.md" "$CODEX_HOME_DIR/hooks/validation.md"
fi

if [[ ! -f "$CODEX_HOME_DIR/AGENTS.md" ]]; then
  cat > "$CODEX_HOME_DIR/AGENTS.md" <<'EOF'
# Global Codex Guidance

EOF
fi

if ! grep -q "Durable Memory Layers" "$CODEX_HOME_DIR/AGENTS.md"; then
  {
    printf '\n'
    cat "$TEMPLATE_DIR/AGENTS.append.md"
  } >> "$CODEX_HOME_DIR/AGENTS.md"
fi

"$PACKAGE_DIR/scripts/check_permissions.sh" --codex-home "$CODEX_HOME_DIR" --maintenance-dir "$MAINTENANCE_DIR"

cat > "$MAINTENANCE_DIR/install-self-check.md" <<EOF
# 自动经验总结安装后自检报告

- 生成时间：$TODAY
- 安装版本：$PACKAGE_VERSION
- Codex Home：$CODEX_HOME_DIR
- 维护目录：$MAINTENANCE_DIR
- 自动化配置：$CODEX_HOME_DIR/automations/development-lesson-review/automation.toml
- 自动化状态：$STATUS
- 调度时间：本地 ${UTC_HOUR}:00
- 观察仓库：${REPOS[*]}
- 主游标：$MAINTENANCE_DIR/lesson-review-cursor.json
- 运行记忆：$CODEX_HOME_DIR/automations/development-lesson-review/memory.md
- 维护面板：$MAINTENANCE_DIR/start_dashboard.py
- 权限检查：已通过

## 升级保护

使用 \`--upgrade\` 时，安装脚本会更新自动化配置、维护面板脚本、权限检查脚本和缺失模板，但不会重置既有 \`memory.md\`、\`lesson-review-cursor.json\`、复盘日志、候选经验或待确认变更。关键文件覆盖前会先生成 \`.bak.时间戳\` 备份。
EOF

echo "安装完成。"
echo "Codex Home: $CODEX_HOME_DIR"
echo "集中维护目录: $MAINTENANCE_DIR"
echo "自动化: $CODEX_HOME_DIR/automations/development-lesson-review/automation.toml"
echo "维护面板: python3 \"$MAINTENANCE_DIR/start_dashboard.py\""
echo "权限检查: \"$MAINTENANCE_DIR/check_permissions.sh\""
echo "安装后自检报告: $MAINTENANCE_DIR/install-self-check.md"
echo "状态: $STATUS"
echo "版本: $PACKAGE_VERSION"
echo "升级模式: $UPGRADE"
echo "调度: 本地 ${UTC_HOUR}:00；当前 Codex App 按本地时间解释 BYHOUR。"
echo "仓库: ${REPOS[*]}"
