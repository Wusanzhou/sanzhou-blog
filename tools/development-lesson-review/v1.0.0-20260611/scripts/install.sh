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
复盘近期 Codex 协作工作，包括 \`$CODEX_HOME_DIR\` 下可用的近期对话/会话记录，以及相关工作区变化。每次运行都应视为无聊天历史状态：不要依赖上一轮 chat 或上一轮自动化线程延续记忆。主游标是 \`$MAINTENANCE_DIR/lesson-review-cursor.json\`；\`$CODEX_HOME_DIR/automations/development-lesson-review/memory.md\` 只作为人工可读运行记忆和最近结论。维护目录保存 \`$MAINTENANCE_DIR/lesson-review-log.md\`、\`$MAINTENANCE_DIR/lesson-review-candidates.md\`、\`$MAINTENANCE_DIR/lesson-review-pending-changes.md\`、\`$MAINTENANCE_DIR/lesson-review-cursor.json\` 和归档内容。

开始时先读取 \`$MAINTENANCE_DIR/lesson-review-cursor.json\` 中最新主游标，并读取 \`$CODEX_HOME_DIR/automations/development-lesson-review/memory.md\` 作为人工可读运行记忆参考。每次运行开始时还必须主动检查本线程收到的运行环境权限说明，记录 \`sandbox_mode\`、\`permission_profile\`、\`writable_roots\` 或 \`danger-full-access\` 状态；如当前线程无法直接看到结构化字段，则说明“本线程上下文未暴露结构化 writable_roots”，并从本轮实际写入结果判断。每次运行结束时必须明确报告主游标 \`$MAINTENANCE_DIR/lesson-review-cursor.json\` 是否写入成功，以及 \`memory.md\` 运行记忆是否写入成功。只处理游标之后的新输入：跟踪文件元数据已变化的 Codex 对话/会话记录、\`last_seen_head\` 之后的仓库提交，以及状态哈希不同于 \`last_seen_status_hash\` 的工作区状态变化。\`development-lesson-review\` 自身产生的常规会话按维护噪声处理，除非其中包含超出游标/日志维护的新持久指导决策。

复盘重点是用户和 Codex 如何协作：重复出现的用户偏好、重复工作流、遗漏的假设、可避免的澄清循环、验证缺口、权限边界和失败模式。默认策略是宁可漏掉弱经验，也不要把噪声写进长期记忆。只提取广泛有用且达到写入门槛的开发经验，并写入正确的持久层。

直接写入持久层前必须先通过降噪门槛。允许直接写入的高置信度经验必须满足以下至少一类：同一偏好/流程/失败模式在多次对话或多次任务中重复出现；用户明确要求“记住”“以后都这样”“写进 AGENTS.md”“做成 skill”或等价表达；某个遗漏造成明显错误、返工、误操作或错误结论，且未来有较大复发可能；内容是稳定权限、隐私、路径、禁止操作、生产环境限制等边界；经验能转成确定性检查、回归样例或固定流程。

以下内容默认不写入持久层：单次任务里的实现细节；一次性的用户表达习惯或临时偏好；没有复发迹象的小偏好；Codex 自己的推测或未验证结论；某个仓库的临时状态；普通成功流程中没有新信息的步骤；已存在的同义经验；只对当前 PR、当前 bug、当前临时上下文有用的信息；太宽泛的空泛建议。

自动复盘不得把敏感信息写入任何持久文件。禁止写入 token、密钥、密码、cookie、授权头、私钥、证书、完整连接串、完整内部接口参数、客户/用户隐私数据；禁止记录敏感原文。如需沉淀经验，只写抽象规则，例如“不要输出密钥内容”。写入前检查常见敏感关键词：\`token\`、\`secret\`、\`password\`、\`passwd\`、\`Authorization\`、\`Bearer\`、\`cookie\`、\`private_key\`、\`AKIA\`、\`BEGIN PRIVATE KEY\`。发现疑似敏感信息时，只在本次总结中说明“发现疑似敏感内容，未写入”，不要写入日志、候选或长期规则。如果无法判断某段内容是否敏感，按敏感处理，不落盘。

写入前必须自检：这条经验是否跨未来任务有用；它是否来自重复信号、用户明确要求、明显返工/错误、稳定边界，或可确定性验证的问题；它是否已经选择了最窄的合适层级，而不是不必要地写入全局层；它是否已在目标文件或 \`$MAINTENANCE_DIR/lesson-review-log.md\` 中以相同/近似形式存在；如果删除这条经验，未来是否真的更容易再次犯错。只有前两项为“是”、层级选择足够窄、查重通过，并且删除后确实更容易复发时，才允许直接写入持久层。中置信度线索只写入 \`$MAINTENANCE_DIR/lesson-review-candidates.md\` 等待人工审查；低置信度线索不写入，只在本次中文总结里说明跳过原因。

写入中置信度候选时，必须包含：来源、候选经验、暂不直接写入原因、建议层级、状态、作用范围、复查时间或过期条件、需要人工确认的问题。状态使用“待审查 / 已采纳 / 已拒绝 / 已过期”；作用范围使用“全局 / 当前仓库 / 当前模块 / 当前任务”。当前任务范围默认不写入长期层。候选超过 60 天仍未采纳时，建议标记为已过期；如果后续出现新证据，可以重新创建候选。

如果新会话中出现与现有长期指导、skill、rules、hooks、vault 状态或历史经验相悖的工作逻辑，不要直接覆盖旧内容，也不要静默忽略。先判断冲突类型：如果它像可能的新经验、例外边界或适用范围调整，写入 \`$MAINTENANCE_DIR/lesson-review-candidates.md\`，状态为“待审查”；如果它意味着需要删除、降级、迁移或修改已有长期内容，写入 \`$MAINTENANCE_DIR/lesson-review-pending-changes.md\`，确认状态为“待确认”。冲突条目必须说明冲突对象、相悖点、新证据、暂不直接执行原因、建议处理方式和需要人工确认的问题。

写入任何会被日常任务默认读取的文件前，必须评估上下文成本。高频上下文文件包括 \`AGENTS.md\`、触发到的 \`skills/*/SKILL.md\`、当前仓库项目指导文件和自动化 prompt。\`AGENTS.md\` 只写短小、稳定、可复用、能改变未来行为的规则；不要写历史、案例、长解释、审计记录或候选内容。全局 \`AGENTS.md\` 建议控制在 1500-2500 字以内，项目 \`AGENTS.md\` 建议控制在 1000-2000 字以内；如果新增内容会让文件明显增长，优先合并或压缩已有规则，而不是追加新段落。写入 \`skills/\` 前必须先查找已有相关 skill；能迭代已有 skill 时优先更新已有 skill，不要因为同类经验创建重复 skill。只有没有合适承载点，或新流程的触发条件、步骤和校验都明显独立时，才创建新 skill。长流程不要全部塞进 \`SKILL.md\`；\`SKILL.md\` 只写核心流程和何时读取参考，详细内容放入 \`references/\`。历史、案例、解释、审计记录、候选内容和长期状态放入 \`vault/\`、\`evals/\`、\`hooks/\` 或 skill references，按需读取，不进入默认上下文。

跨项目通用经验才写入 \`$CODEX_HOME_DIR\` 下的全局文件：重复偏好写入 \`AGENTS.md\`，重复工作流写入 \`skills/\`，持久状态和决策写入 \`vault/\`，可复现失败案例写入 \`evals/\`，权限期望写入 \`rules/\`，确定性检查写入 \`hooks/\`。仓库专属经验优先写入该仓库本地持久层：项目指导写入 \`AGENTS.md\`，重复工作流写入 \`skills/\`，稳定项目状态和决策写入 \`vault/\`，回归案例写入 \`evals/\`，权限/访问边界写入 \`rules/\`，确定性校验写入 \`hooks/\`。

写入任何经验前，先检查目标持久文件和 \`$MAINTENANCE_DIR/lesson-review-log.md\`；如果相同或实质等价的经验已经存在，不要重复写入。自动总结和持久指导更新中，正文内容（规则、边界、经验说明、分层理由、校验说明等）使用中文书写，方便后续审查。必要的文件名、标识符、技术术语、章节标题或简短简介可以继续使用英文。

判断游标是否可写时，重点检查主游标 \`$MAINTENANCE_DIR/lesson-review-cursor.json\`，并检查 \`$CODEX_HOME_DIR/automations/development-lesson-review/memory.md\` 是否可写以便记录中文运行摘要。写主游标时先写临时 JSON 文件，校验能被解析后再替换目标文件，避免半写入导致游标损坏。

长期项目需要定期整理自动复盘材料，避免日志、候选和规则无限增长。每月进行一次压缩整理：汇总上月日志、清理已拒绝/已过期候选、合并重复经验、把稳定流程整理进 \`skills/\`、把失败案例整理进 \`evals/\`、归档旧日志。旧日志和旧候选按月份放入 \`$MAINTENANCE_DIR/archive/\`，当前文件只保留最近 1-2 个月便于审查。月度整理时必须检查规则冲突：全局 \`AGENTS.md\` 与项目 \`AGENTS.md\` 是否矛盾，\`skills/\` 与 \`hooks/\` 是否重复或冲突，项目规则是否应覆盖全局规则，旧规则是否已过期。可以提出“建议删除”“建议降级为候选”“建议从全局迁移到项目本地”，但不要自动执行删除或迁移，除非用户明确确认；这些建议必须写入 \`$MAINTENANCE_DIR/lesson-review-pending-changes.md\`，包含建议动作、原文件、原内容摘要、建议目标、理由、风险、确认状态、处理结论和处理时间。

只要修改了任何持久指导文件，就向 \`$MAINTENANCE_DIR/lesson-review-log.md\` 追加一条简洁中文记录，包含：来源、变更文件、经验、分层理由、校验。如果只写入候选文件或待确认变更，也要在本次回复中说明候选条目、待确认动作和暂不直接执行原因。如果没有持久指导文件变更，不要追加日志条目。每次复盘结束后，都要把新的主游标写入 \`$MAINTENANCE_DIR/lesson-review-cursor.json\`，包含本轮已复核到的时间、文件元数据摘要、仓库 head/status、是否发现新长期经验。主游标写入成功后，再更新 \`$CODEX_HOME_DIR/automations/development-lesson-review/memory.md\` 作为中文运行摘要。只有主游标写入失败时，才报告自动化 cursor 无法推进；此时不要写入新的长期经验，避免重复沉淀。

保持变更简洁，避免一次性、重复或猜测性记录；不要持久化私有推理；保留用户已有修改。每次运行结束时，用中文简短回复本次检查了什么、直接修改了哪些持久文件、写入了哪些候选或待确认变更、哪些内容因重复/一次性/证据不足/范围过宽/上下文成本过高/疑似敏感被跳过，发现了哪些规则冲突，提出了哪些删除/降级/迁移建议，cursor 是否已更新，以及是否发现权限或写入失败。
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
