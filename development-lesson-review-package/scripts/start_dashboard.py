#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
import webbrowser


FILES = {
    "log": {
        "title": "复盘日志",
        "path": "lesson-review-log.md",
        "description": "查看每次自动复盘实际修改了什么、为什么修改、如何校验。",
    },
    "candidates": {
        "title": "候选经验",
        "path": "lesson-review-candidates.md",
        "description": "处理中置信度线索，决定是否采纳、拒绝或标记过期。",
    },
    "pending": {
        "title": "待确认变更",
        "path": "lesson-review-pending-changes.md",
        "description": "确认自动化提出的删除、降级或迁移建议。",
    },
    "cursor": {
        "title": "复盘游标",
        "path": "lesson-review-cursor.json",
        "description": "查看机器可读的复盘进度副本；主连续记忆仍以 memory.md 为准。",
    },
    "memory": {
        "title": "自动化记忆",
        "path": "__AUTOMATION_MEMORY__",
        "description": "查看自动复盘主游标和运行记忆。这是判断复盘进度的权威来源。",
    },
    "archive_readme": {
        "title": "归档说明",
        "path": "archive/README.md",
        "description": "查看旧日志和候选经验的归档规则。",
    },
}


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>自动经验总结维护面板</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f8f3ed;
      --bg-soft: #fbf8f4;
      --panel: #fffefd;
      --panel-warm: #fff9f4;
      --text: #2d2520;
      --muted: #756b61;
      --line: #eadfD4;
      --line-strong: #dccbbb;
      --accent: #b85c38;
      --accent-dark: #8f3f22;
      --accent-soft: #fff0e7;
      --accent-line: #e0a186;
      --shadow: 0 18px 50px rgba(63, 45, 32, .09);
      --shadow-soft: 0 8px 22px rgba(63, 45, 32, .06);
      --danger: #b42318;
      --ok: #157a55;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(184, 92, 56, .10), transparent 32rem),
        linear-gradient(135deg, var(--bg), #f4efe7 48%, #f6f1ec);
      color: var(--text);
      min-height: 100vh;
    }
    header {
      padding: 22px 28px 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 254, 253, .82);
      backdrop-filter: blur(14px);
      position: sticky;
      top: 0;
      z-index: 2;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 680;
      letter-spacing: 0;
    }
    .sub {
      margin-top: 7px;
      color: var(--muted);
      font-size: 13px;
      word-break: break-all;
      overflow-wrap: anywhere;
    }
    main {
      display: grid;
      grid-template-columns: minmax(240px, 300px) 1fr;
      gap: 18px;
      padding: 18px;
      min-height: calc(100vh - 88px);
    }
    nav, section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow-soft);
    }
    nav {
      padding: 10px;
      align-self: start;
    }
    .item {
      width: 100%;
      border: 1px solid transparent;
      background: transparent;
      text-align: left;
      padding: 11px 12px;
      border-radius: 6px;
      cursor: pointer;
      margin-bottom: 7px;
      transition: background .16s ease, border-color .16s ease, box-shadow .16s ease;
    }
    .item:hover {
      background: var(--bg-soft);
      border-color: var(--line);
    }
    .item.active {
      border-color: var(--accent-line);
      background: var(--accent-soft);
      box-shadow: inset 3px 0 0 var(--accent);
    }
    .item strong {
      display: block;
      font-size: 14px;
      font-weight: 650;
      margin-bottom: 5px;
      color: #332821;
    }
    .item span {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    section {
      display: flex;
      flex-direction: column;
      min-width: 0;
      overflow: hidden;
      box-shadow: var(--shadow);
    }
    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, var(--panel), var(--panel-warm));
    }
    .title { min-width: 0; }
    .title h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 680;
      letter-spacing: 0;
    }
    .path {
      color: var(--muted);
      font-size: 12px;
      margin-top: 5px;
      word-break: break-all;
    }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    button {
      border: 1px solid var(--line);
      background: #fffdfb;
      color: var(--text);
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 560;
      transition: transform .12s ease, background .16s ease, border-color .16s ease, box-shadow .16s ease;
    }
    button:hover {
      background: #fff8f2;
      border-color: var(--line-strong);
      box-shadow: 0 4px 12px rgba(63, 45, 32, .07);
    }
    button:active { transform: translateY(1px); }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
      box-shadow: 0 8px 18px rgba(184, 92, 56, .22);
    }
    button.primary:hover {
      background: var(--accent-dark);
      border-color: var(--accent-dark);
    }
    button:disabled { opacity: .6; cursor: not-allowed; }
    textarea {
      flex: 1;
      width: 100%;
      min-height: 520px;
      border: 0;
      padding: 18px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
      line-height: 1.65;
      outline: none;
      color: #2b2622;
      background:
        linear-gradient(90deg, rgba(184, 92, 56, .05) 0, rgba(184, 92, 56, .05) 1px, transparent 1px),
        #fffdfb;
      background-size: 42px 100%;
    }
    .status {
      padding: 10px 14px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
      min-height: 38px;
      background: var(--panel-warm);
    }
    .status.ok { color: var(--ok); }
    .status.err { color: var(--danger); }
    @media (max-width: 800px) {
      header { padding: 18px 18px 14px; }
      main {
        grid-template-columns: 1fr;
        padding: 12px;
      }
      .toolbar {
        align-items: flex-start;
        flex-direction: column;
      }
      .actions { width: 100%; justify-content: flex-start; }
      textarea { min-height: 420px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>自动经验总结维护面板</h1>
    <div class="sub" id="rootText">正在读取维护目录...</div>
  </header>
  <main>
    <nav id="nav"></nav>
    <section>
      <div class="toolbar">
        <div class="title">
          <h2 id="fileTitle">请选择文件</h2>
          <div class="path" id="filePath"></div>
        </div>
        <div class="actions">
          <button id="reloadBtn">重新读取</button>
          <button id="saveBtn" class="primary">保存修改</button>
        </div>
      </div>
      <textarea id="editor" spellcheck="false"></textarea>
      <div class="status" id="status"></div>
    </section>
  </main>
  <script>
    let files = {};
    let current = null;
    let dirty = false;
    const nav = document.getElementById("nav");
    const editor = document.getElementById("editor");
    const statusEl = document.getElementById("status");
    const fileTitle = document.getElementById("fileTitle");
    const filePath = document.getElementById("filePath");
    const rootText = document.getElementById("rootText");

    function setStatus(text, kind = "") {
      statusEl.textContent = text;
      statusEl.className = "status " + kind;
    }

    async function api(path, options) {
      const res = await fetch(path, options);
      const text = await res.text();
      if (!res.ok) throw new Error(text || res.statusText);
      return text ? JSON.parse(text) : {};
    }

    function renderNav() {
      nav.innerHTML = "";
      for (const [id, meta] of Object.entries(files)) {
        const btn = document.createElement("button");
        btn.className = "item" + (id === current ? " active" : "");
        btn.innerHTML = `<strong>${meta.title}</strong><span>${meta.description}</span>`;
        btn.onclick = () => selectFile(id);
        nav.appendChild(btn);
      }
    }

    async function selectFile(id) {
      if (dirty && !confirm("当前文件有未保存修改，确定切换吗？")) return;
      current = id;
      renderNav();
      await loadFile();
    }

    async function loadFile() {
      if (!current) return;
      const meta = files[current];
      fileTitle.textContent = meta.title;
      filePath.textContent = meta.path;
      editor.value = "";
      dirty = false;
      setStatus("正在读取...");
      try {
        const data = await api(`/api/file?id=${encodeURIComponent(current)}`);
        editor.value = data.content;
        setStatus("已读取。", "ok");
      } catch (err) {
        setStatus("读取失败：" + err.message, "err");
      }
    }

    async function saveFile() {
      if (!current) return;
      setStatus("正在保存...");
      try {
        await api(`/api/file?id=${encodeURIComponent(current)}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: editor.value })
        });
        dirty = false;
        setStatus("已保存。", "ok");
      } catch (err) {
        setStatus("保存失败：" + err.message, "err");
      }
    }

    editor.addEventListener("input", () => {
      dirty = true;
      setStatus("有未保存修改。");
    });
    document.getElementById("reloadBtn").onclick = loadFile;
    document.getElementById("saveBtn").onclick = saveFile;

    async function init() {
      try {
        const data = await api("/api/files");
        files = data.files;
        rootText.textContent = "维护目录：" + data.root;
        renderNav();
        const first = Object.keys(files)[0];
        if (first) await selectFile(first);
      } catch (err) {
        setStatus("初始化失败：" + err.message, "err");
      }
    }
    init();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        if isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status, payload):
        self._send(status, json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8")

    def _file_path(self):
        query = urlparse(self.path).query
        params = dict(item.split("=", 1) for item in query.split("&") if "=" in item)
        file_id = unquote(params.get("id", ""))
        if file_id not in FILES:
            return None
        if file_id == "memory":
            path = (self.server.codex_home / "automations" / "development-lesson-review" / "memory.md").resolve()
            if not str(path).startswith(str(self.server.codex_home.resolve())):
                return None
            return path
        path = (self.server.root / FILES[file_id]["path"]).resolve()
        if not str(path).startswith(str(self.server.root.resolve())):
            return None
        return path

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, INDEX_HTML, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/files":
            self._json(200, {"root": str(self.server.root), "files": FILES})
            return
        if parsed.path == "/api/file":
            path = self._file_path()
            if path is None:
                self._send(404, "未知文件", "text/plain; charset=utf-8")
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("", encoding="utf-8")
            self._json(200, {"content": path.read_text(encoding="utf-8")})
            return
        self._send(404, "未找到", "text/plain; charset=utf-8")

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/file":
            self._send(404, "未找到", "text/plain; charset=utf-8")
            return
        path = self._file_path()
        if path is None:
            self._send(404, "未知文件", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        content = payload.get("content", "")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._json(200, {"ok": True})

    def log_message(self, fmt, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="启动自动经验总结维护面板")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--maintenance-dir", default=os.environ.get("LESSON_REVIEW_HOME"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    if args.maintenance_dir:
        root = Path(args.maintenance_dir)
    else:
        root = Path(args.codex_home) / "automations" / "development-lesson-review" / "maintenance"
    root.mkdir(parents=True, exist_ok=True)
    (root / "archive").mkdir(parents=True, exist_ok=True)
    for meta in FILES.values():
        if meta["path"] == "__AUTOMATION_MEMORY__":
            continue
        path = root / meta["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.root = root
    server.codex_home = Path(args.codex_home)
    url = f"http://{args.host}:{args.port}/"
    print(f"维护面板已启动：{url}")
    print(f"维护目录：{root}")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
