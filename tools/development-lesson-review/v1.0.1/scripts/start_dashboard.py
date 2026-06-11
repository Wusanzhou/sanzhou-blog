#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from datetime import datetime
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
    "memory": {
        "title": "自动化记忆",
        "path": "__AUTOMATION_MEMORY__",
        "description": "查看自动复盘运行记忆和最近结论，用于辅助排查每轮做了什么。",
    },
    "archive_readme": {
        "title": "归档说明",
        "path": "archive/README.md",
        "description": "查看旧日志和候选经验的归档规则。",
    },
    "cursor": {
        "title": "复盘游标",
        "path": "lesson-review-cursor.json",
        "description": "查看机器可读的稳定复盘进度，自动化用它判断下次从哪里继续。",
    },
}

STRUCTURED_FILES = {"log", "candidates", "pending", "cursor", "memory", "archive_readme"}


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
      padding: 16px 28px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 254, 253, .82);
      backdrop-filter: blur(14px);
      position: sticky;
      top: 0;
      z-index: 2;
      display: grid;
      grid-template-columns: max-content minmax(0, 1fr);
      align-items: center;
      column-gap: 32px;
    }
    .brand { min-width: 0; }
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
      display: block;
      padding: 18px;
      min-height: calc(100vh - 88px);
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow-soft);
    }
    nav {
      display: flex;
      gap: 9px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
    }
    .item {
      border: 1px solid transparent;
      background: rgba(255, 253, 251, .86);
      text-align: center;
      padding: 9px 13px;
      border-radius: 999px;
      cursor: pointer;
      margin-bottom: 0;
      transition: background .16s ease, border-color .16s ease, box-shadow .16s ease;
    }
    .item:hover {
      background: var(--bg-soft);
      border-color: var(--line);
    }
    .item.active {
      border-color: var(--accent-line);
      background: var(--accent-soft);
      box-shadow: 0 6px 16px rgba(184, 92, 56, .14);
    }
    .item strong {
      display: block;
      font-size: 14px;
      font-weight: 650;
      margin-bottom: 0;
      color: #332821;
    }
    .more-wrap {
      position: relative;
      display: inline-flex;
    }
    .more-menu {
      position: absolute;
      right: 0;
      top: calc(100% + 8px);
      z-index: 20;
      display: none;
      min-width: 176px;
      padding: 8px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 254, 253, .98);
      box-shadow: var(--shadow);
    }
    .more-menu.open { display: grid; gap: 6px; }
    .more-menu button {
      width: 100%;
      text-align: left;
      border-color: transparent;
      background: transparent;
      border-radius: 6px;
    }
    .more-menu button:hover {
      background: var(--accent-soft);
      border-color: var(--accent-line);
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
    .desc {
      color: #5f554d;
      font-size: 14px;
      line-height: 1.55;
      margin-top: 7px;
      max-width: 720px;
    }
    .file-ref {
      color: var(--muted);
      font-size: 12px;
      margin-top: 5px;
      overflow-wrap: anywhere;
    }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
    .tools {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
      padding: 10px 16px;
      border-bottom: 1px solid var(--line);
      background: #fffdfb;
    }
    .tools-left,
    .tools-pagination {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .tools-left { min-width: min(460px, 100%); }
    .tools-pagination {
      justify-content: flex-end;
      margin-left: auto;
    }
    .tools input, .tools select {
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fffdfb;
      color: var(--text);
      padding: 8px 10px;
      font-size: 13px;
      min-height: 36px;
    }
    .tools input { min-width: min(320px, 100%); }
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
    .secondary { color: var(--muted); }
    .danger {
      border-color: rgba(180, 35, 24, .28);
      color: var(--danger);
      background: #fff7f6;
    }
    .success {
      border-color: rgba(21, 122, 85, .25);
      color: var(--ok);
      background: #f3fbf7;
    }
    .structured {
      display: none;
      flex: 1;
      overflow: auto;
      padding: 16px;
      background: #fffdfb;
    }
    .summary {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }
    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      background: var(--panel-warm);
      color: var(--muted);
      font-size: 12px;
    }
    .filter-btn {
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      background: var(--panel-warm);
    }
    .filter-btn.active {
      color: white;
      background: var(--accent);
      border-color: var(--accent);
      box-shadow: 0 5px 12px rgba(184, 92, 56, .18);
    }
    .empty {
      border: 1px dashed var(--line-strong);
      border-radius: 8px;
      padding: 28px;
      color: var(--muted);
      background: var(--panel-warm);
      text-align: center;
    }
    .record {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow-soft);
      margin-bottom: 14px;
      overflow: hidden;
    }
    .record-head {
      display: flex;
      gap: 12px;
      justify-content: space-between;
      align-items: flex-start;
      padding: 13px 14px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, #fffefd, #fff8f2);
    }
    .record-title {
      min-width: 0;
      font-weight: 680;
      font-size: 15px;
      line-height: 1.4;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      white-space: nowrap;
      border-radius: 999px;
      padding: 4px 9px;
      font-size: 12px;
      border: 1px solid var(--line);
      color: var(--muted);
      background: #fffdfb;
    }
    .badge.good { color: var(--ok); border-color: rgba(21, 122, 85, .25); background: #f3fbf7; }
    .badge.bad { color: var(--danger); border-color: rgba(180, 35, 24, .25); background: #fff7f6; }
    .badge.wait { color: var(--accent-dark); border-color: var(--accent-line); background: var(--accent-soft); }
    .record-body {
      padding: 12px 14px 6px;
      display: grid;
      gap: 8px;
    }
    .field {
      display: grid;
      grid-template-columns: 140px minmax(0, 1fr);
      gap: 12px;
      border-bottom: 1px solid rgba(234, 223, 212, .65);
      padding-bottom: 7px;
    }
    .field:last-child { border-bottom: 0; }
    .field-name {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }
    .field-value {
      color: var(--text);
      font-size: 13px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .record-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 12px 14px 14px;
      background: #fffdfb;
    }
    .record-pre {
      margin: 0;
      color: var(--text);
      font-size: 13px;
      line-height: 1.65;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
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
      header {
        padding: 18px 18px 14px;
        grid-template-columns: 1fr;
        row-gap: 14px;
      }
      main {
        padding: 12px;
      }
      nav { gap: 7px; justify-content: flex-start; }
      .item { padding: 8px 10px; }
      .more-menu {
        left: 0;
        right: auto;
      }
      .toolbar {
        align-items: flex-start;
        flex-direction: column;
      }
      .actions { width: 100%; justify-content: flex-start; }
      .tools-left,
      .tools-pagination { width: 100%; justify-content: flex-start; }
      .tools input { width: 100%; }
      textarea { min-height: 420px; }
      .field { grid-template-columns: 1fr; gap: 3px; }
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1>自动经验总结维护面板</h1>
    </div>
    <nav id="nav"></nav>
  </header>
  <main>
    <section>
      <div class="toolbar">
        <div class="title">
          <h2 id="fileTitle">请选择文件</h2>
          <div class="path" id="filePath"></div>
        </div>
        <div class="actions">
          <button id="reloadBtn">重新读取</button>
          <button id="rawBtn" class="secondary">原文编辑</button>
          <button id="saveBtn" class="primary">保存修改</button>
        </div>
      </div>
      <div class="tools">
        <div class="tools-left">
          <input id="searchInput" type="search" placeholder="搜索当前页面记录" />
          <select id="timeFilter">
            <option value="all">全部时间</option>
            <option value="7d">最近 7 天</option>
            <option value="30d">最近 30 天</option>
            <option value="this_month">本月</option>
            <option value="last_month">上月</option>
          </select>
        </div>
        <div id="paginationBar" class="tools-pagination"></div>
      </div>
      <div id="structuredView" class="structured"></div>
      <textarea id="editor" spellcheck="false"></textarea>
      <div class="status" id="status"></div>
    </section>
  </main>
  <script>
    let files = {};
    let current = null;
    let dirty = false;
    let rawMode = false;
    let activeFilter = "全部";
    let searchText = "";
    let timeFilter = "all";
    let currentPage = 1;
    let pageSize = 10;
    const nav = document.getElementById("nav");
    const editor = document.getElementById("editor");
    const structuredView = document.getElementById("structuredView");
    const statusEl = document.getElementById("status");
    const fileTitle = document.getElementById("fileTitle");
    const filePath = document.getElementById("filePath");
    const rawBtn = document.getElementById("rawBtn");
    const saveBtn = document.getElementById("saveBtn");
    const searchInput = document.getElementById("searchInput");
    const timeFilterSelect = document.getElementById("timeFilter");
    const paginationBar = document.getElementById("paginationBar");
    const structuredFiles = new Set(["log", "candidates", "pending", "cursor", "memory", "archive_readme"]);
    const primaryNavIds = ["log", "candidates", "pending", "memory"];
    const extraNavIds = new Set(["archive_readme", "cursor"]);

    function setStatus(text, kind = "") {
      statusEl.textContent = text;
      statusEl.className = "status " + kind;
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    async function api(path, options) {
      const res = await fetch(path, options);
      const text = await res.text();
      if (!res.ok) throw new Error(text || res.statusText);
      return text ? JSON.parse(text) : {};
    }

    function renderNav() {
      nav.innerHTML = "";
      for (const id of primaryNavIds) {
        const meta = files[id];
        if (!meta) continue;
        const btn = document.createElement("button");
        btn.className = "item" + (id === current ? " active" : "");
        btn.innerHTML = `<strong>${meta.title}</strong>`;
        btn.onclick = () => selectFile(id);
        nav.appendChild(btn);
      }
      const wrap = document.createElement("div");
      wrap.className = "more-wrap";
      const moreActive = extraNavIds.has(current);
      wrap.innerHTML = `
        <button class="item${moreActive ? " active" : ""}" id="moreBtn" type="button" aria-haspopup="menu" aria-expanded="false"><strong>更多功能</strong></button>
        <div class="more-menu" id="moreMenu" role="menu">
          <button type="button" data-action="archive_readme">归档说明</button>
          <button type="button" data-action="cursor">复盘游标</button>
          <button type="button" data-action="self_check">安装自检</button>
          <button type="button" data-action="backup">备份</button>
          <button type="button" data-action="archive">归档</button>
          <button type="button" data-action="paths">路径导航</button>
          <button type="button" data-action="rule_check">规则冲突检查</button>
        </div>
      `;
      const moreBtn = wrap.querySelector("#moreBtn");
      const moreMenu = wrap.querySelector("#moreMenu");
      moreBtn.onclick = (event) => {
        event.stopPropagation();
        const isOpen = moreMenu.classList.toggle("open");
        moreBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
      };
      moreMenu.onclick = async (event) => {
        const action = event.target.dataset.action;
        if (!action) return;
        moreMenu.classList.remove("open");
        moreBtn.setAttribute("aria-expanded", "false");
        if (action === "archive_readme" || action === "cursor") {
          await selectFile(action);
        } else if (action === "self_check") {
          await showSelfCheck();
        } else if (action === "backup") {
          await showBackups();
        } else if (action === "archive") {
          await runArchive();
        } else if (action === "paths") {
          await showPathNavigator();
        } else if (action === "rule_check") {
          await showRuleCheck();
        }
      };
      nav.appendChild(wrap);
    }

    document.addEventListener("click", () => {
      const moreMenu = document.getElementById("moreMenu");
      const moreBtn = document.getElementById("moreBtn");
      if (!moreMenu || !moreBtn) return;
      moreMenu.classList.remove("open");
      moreBtn.setAttribute("aria-expanded", "false");
    });

    async function selectFile(id) {
      if (dirty && !confirm("当前文件有未保存修改，确定切换吗？")) return;
      current = id;
      rawMode = false;
      activeFilter = "全部";
      searchText = "";
      timeFilter = "all";
      currentPage = 1;
      searchInput.value = "";
      timeFilterSelect.value = "all";
      renderNav();
      await loadFile();
    }

    function parseRecords(content) {
      const marker = "\n## 记录";
      const idx = content.indexOf(marker);
      const headEnd = idx >= 0 ? content.indexOf("\n", idx + marker.length) : -1;
      const prefix = headEnd >= 0 ? content.slice(0, headEnd + 1) : "";
      const body = headEnd >= 0 ? content.slice(headEnd + 1) : content;
      const matches = [...body.matchAll(/^### .+$/gm)];
      const records = [];
      if (!matches.length) return { prefix, records };
      for (let i = 0; i < matches.length; i++) {
        const start = matches[i].index;
        const end = i + 1 < matches.length ? matches[i + 1].index : body.length;
        const raw = body.slice(start, end).trim();
        const lines = raw.split(/\n/);
        const title = lines[0].replace(/^###\s*/, "").trim();
        const fields = {};
        const rest = [];
        for (const line of lines.slice(1)) {
          const m = line.match(/^- ([^：:]+)[：:]\s*(.*)$/);
          if (m) fields[m[1].trim()] = m[2].trim();
          else if (line.trim()) rest.push(line);
        }
        records.push({ index: i, title, raw, fields, rest: rest.join("\n").trim() });
      }
      return { prefix, records };
    }

    function parseSections(content) {
      const matches = [...content.matchAll(/^#{1,3} .+$/gm)];
      if (!matches.length) return [];
      const sections = [];
      for (let i = 0; i < matches.length; i++) {
        const start = matches[i].index;
        const end = i + 1 < matches.length ? matches[i + 1].index : content.length;
        const raw = content.slice(start, end).trim();
        const lines = raw.split(/\n/);
        sections.push({
          index: i,
          title: lines[0].replace(/^#{1,3}\s*/, "").trim(),
          raw,
          body: lines.slice(1).join("\n").trim()
        });
      }
      return sections;
    }

    function parseTimeBlocks(content) {
      const matches = [...content.matchAll(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?:\s+[A-Z]{2,5})?$/gm)];
      if (!matches.length) return [];
      const blocks = [];
      for (let i = 0; i < matches.length; i++) {
        const start = matches[i].index;
        const end = i + 1 < matches.length ? matches[i + 1].index : content.length;
        const raw = content.slice(start, end).trim();
        const lines = raw.split(/\n/);
        blocks.push({
          index: i,
          title: lines[0].trim(),
          body: lines.slice(1).join("\n").trim()
        });
      }
      return blocks;
    }

    function buildContent(prefix, records) {
      const body = records.map(r => r.raw.trim()).filter(Boolean).join("\n\n");
      return prefix.trimEnd() + "\n\n" + body + (body ? "\n" : "");
    }

    function updateRecordRaw(record, updates) {
      const lines = record.raw.split(/\n/);
      for (const [field, value] of Object.entries(updates)) {
        const idx = lines.findIndex(line => line.startsWith(`- ${field}：`) || line.startsWith(`- ${field}:`));
        const next = `- ${field}：${value}`;
        if (idx >= 0) lines[idx] = next;
        else lines.push(next);
      }
      return lines.join("\n");
    }

    function nowText() {
      const d = new Date();
      const pad = n => String(n).padStart(2, "0");
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }

    function parseRecordTime(title) {
      const m = String(title || "").match(/^(\d{4})-(\d{2})-(\d{2})(?:\s+(\d{2}):(\d{2}))?/);
      if (!m) return null;
      return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4] || 0), Number(m[5] || 0));
    }

    function sortNewestFirst(items) {
      return [...items].sort((a, b) => {
        const at = parseRecordTime(a.title)?.getTime();
        const bt = parseRecordTime(b.title)?.getTime();
        if (at == null && bt == null) return b.index - a.index;
        if (at == null) return 1;
        if (bt == null) return -1;
        return bt - at || b.index - a.index;
      });
    }

    function matchSearch(text) {
      const q = searchText.trim().toLowerCase();
      return !q || String(text || "").toLowerCase().includes(q);
    }

    function matchTime(title) {
      if (timeFilter === "all") return true;
      const d = parseRecordTime(title);
      if (!d) return true;
      const now = new Date();
      const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      if (timeFilter === "7d") return d >= new Date(startOfToday.getTime() - 6 * 86400000);
      if (timeFilter === "30d") return d >= new Date(startOfToday.getTime() - 29 * 86400000);
      if (timeFilter === "this_month") return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
      if (timeFilter === "last_month") {
        const last = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        return d.getFullYear() === last.getFullYear() && d.getMonth() === last.getMonth();
      }
      return true;
    }

    function statusClass(status) {
      if (["已采纳", "已确认", "已处理", "已归档"].includes(status)) return "good";
      if (["已拒绝", "已删除", "已过期"].includes(status)) return "bad";
      return "wait";
    }

    function renderStructured() {
      if (!structuredFiles.has(current) || rawMode) {
        structuredView.style.display = "none";
        editor.style.display = "block";
        paginationBar.innerHTML = "";
        rawBtn.style.display = structuredFiles.has(current) ? "inline-block" : "none";
        rawBtn.textContent = "卡片视图";
        saveBtn.style.display = "inline-block";
        return;
      }
      editor.style.display = "none";
      structuredView.style.display = "block";
      rawBtn.style.display = "inline-block";
      rawBtn.textContent = "原文编辑";
      saveBtn.style.display = "none";
      if (current === "cursor") {
        paginationBar.innerHTML = "";
        renderCursor();
        return;
      }
      if (current === "memory") {
        paginationBar.innerHTML = "";
        renderMemory();
        return;
      }
      const parsed = parseRecords(editor.value);
      const records = parsed.records;
      if (!records.length && current === "archive_readme") {
        renderSections();
        return;
      }
      const statusField = current === "candidates" ? "状态" : current === "pending" ? "确认状态" : "";
      const counts = {};
      for (const r of records) {
        if (statusField) {
          const s = r.fields[statusField] || "未填写";
          counts[s] = (counts[s] || 0) + 1;
        }
      }
      const filteredRecords = statusField && activeFilter !== "全部"
        ? records.filter(r => (r.fields[statusField] || "未填写") === activeFilter)
        : records;
      const visibleRecords = sortNewestFirst(filteredRecords.filter(r => matchSearch(r.raw) && matchTime(r.title)));
      const totalPages = Math.max(1, Math.ceil(visibleRecords.length / pageSize));
      if (currentPage > totalPages) currentPage = totalPages;
      const pageStart = (currentPage - 1) * pageSize;
      const pageRecords = visibleRecords.slice(pageStart, pageStart + pageSize);
      const summary = buildSummary(records, counts, statusField);
      if (!records.length) {
        paginationBar.innerHTML = "";
        structuredView.innerHTML = `<div class="summary"><span class="pill">记录：0</span></div><div class="empty">当前没有可展示记录。可以切换到原文编辑查看模板。</div>`;
        return;
      }
      paginationBar.innerHTML = visibleRecords.length ? paginationHtml(visibleRecords.length, totalPages) : "";
      structuredView.innerHTML = `
        ${summary ? `<div class="summary">${summary}</div>` : ""}
        ${visibleRecords.length ? pageRecords.map(recordHtml).join("") : `<div class="empty">当前筛选条件下没有记录。</div>`}
      `;
    }

    function buildSummary(records, counts, statusField) {
      if (!statusField) return "";
      const order = current === "candidates"
        ? ["全部", "待审查", "已采纳", "已拒绝", "已过期", "已删除", "未填写"]
        : ["全部", "待确认", "已确认", "已处理", "已拒绝", "已归档", "未填写"];
      const seen = new Set(["全部", ...Object.keys(counts)]);
      const statuses = order.filter(s => seen.has(s)).concat([...seen].filter(s => !order.includes(s)));
      const buttons = statuses.map(status => {
        const count = status === "全部" ? records.length : (counts[status] || 0);
        return `<button class="filter-btn ${activeFilter === status ? "active" : ""}" onclick="setFilter('${escapeHtml(status)}')">${escapeHtml(status)}：${count}</button>`;
      }).join("");
      return buttons;
    }

    function setFilter(status) {
      activeFilter = status;
      currentPage = 1;
      renderStructured();
    }

    function paginationHtml(total, totalPages) {
      const start = total ? (currentPage - 1) * pageSize + 1 : 0;
      const end = Math.min(total, currentPage * pageSize);
      return `
        <span class="pill">显示：${start}-${end} / ${total}</span>
        <button class="filter-btn" onclick="setPage(1)" ${currentPage <= 1 ? "disabled" : ""}>首页</button>
        <button class="filter-btn" onclick="setPage(${currentPage - 1})" ${currentPage <= 1 ? "disabled" : ""}>上一页</button>
        <span class="pill">第 ${currentPage} / ${totalPages} 页</span>
        <button class="filter-btn" onclick="setPage(${currentPage + 1})" ${currentPage >= totalPages ? "disabled" : ""}>下一页</button>
        <button class="filter-btn" onclick="setPage(${totalPages})" ${currentPage >= totalPages ? "disabled" : ""}>末页</button>
        <select onchange="setPageSize(this.value)">
          ${[10, 20, 50, 100].map(size => `<option value="${size}" ${pageSize === size ? "selected" : ""}>每页 ${size}</option>`).join("")}
        </select>
      `;
    }

    function setPage(page) {
      currentPage = Math.max(1, Number(page) || 1);
      renderStructured();
    }

    function setPageSize(size) {
      pageSize = Number(size) || 10;
      currentPage = 1;
      renderStructured();
    }

    function recordHtml(record) {
      const meta = recordMeta(record);
      return `
        <article class="record">
          <div class="record-head">
            <div class="record-title">${escapeHtml(record.title)}</div>
            <span class="badge ${statusClass(meta.badge)}">${escapeHtml(meta.badge)}</span>
          </div>
          <div class="record-body">
            ${meta.fields.map(name => `
              <div class="field">
                <div class="field-name">${escapeHtml(name)}</div>
                <div class="field-value">${escapeHtml(record.fields[name] || "")}</div>
              </div>
            `).join("")}
            ${record.rest ? `<pre class="record-pre">${escapeHtml(record.rest)}</pre>` : ""}
          </div>
          ${meta.actions ? `<div class="record-actions">${meta.actions}</div>` : ""}
        </article>
      `;
    }

    function recordMeta(record) {
      if (current === "candidates") {
        const status = record.fields["状态"] || "未填写";
        return {
          badge: status,
          fields: ["来源", "候选经验", "暂不直接写入原因", "建议层级", "状态", "作用范围", "复查时间", "过期条件", "需要人工确认的问题", "审查结论", "处理时间"],
          actions: `<button class="success" onclick="setRecordStatus(${record.index}, '已采纳')">采纳</button>
             <button class="danger" onclick="setRecordStatus(${record.index}, '已拒绝')">拒绝</button>
             <button onclick="setRecordStatus(${record.index}, '已过期')">过期</button>
             <button onclick="setRecordStatus(${record.index}, '待审查')">恢复待审查</button>
             <button class="danger" onclick="setRecordStatus(${record.index}, '已删除')">删除</button>`
        };
      }
      if (current === "pending") {
        const status = record.fields["确认状态"] || "未填写";
        return {
          badge: status,
          fields: ["建议动作", "原文件", "原内容摘要", "建议目标", "理由", "风险", "确认状态", "处理结论", "处理时间"],
          actions: `<button class="success" onclick="setRecordStatus(${record.index}, '已确认')">确认</button>
             <button class="danger" onclick="setRecordStatus(${record.index}, '已拒绝')">拒绝</button>
             <button onclick="setRecordStatus(${record.index}, '已处理')">已处理</button>
             <button onclick="setRecordStatus(${record.index}, '待确认')">恢复待确认</button>
             <button onclick="setRecordStatus(${record.index}, '已归档')">归档</button>`
        };
      }
      if (current === "log") {
        return {
          badge: record.fields["变更文件"] ? "已记录" : "记录",
          fields: ["来源", "变更文件", "经验", "分层理由", "校验"],
          actions: ""
        };
      }
      return {
        badge: "记录",
        fields: Object.keys(record.fields),
        actions: ""
      };
    }

    function renderSections() {
      paginationBar.innerHTML = "";
      const sections = parseSections(editor.value);
      if (!sections.length) {
        if (editor.value.trim()) {
          structuredView.innerHTML = `
            <div class="summary"><span class="pill">模块：1</span></div>
            <article class="record">
              <div class="record-head">
                <div class="record-title">全文内容</div>
                <span class="badge">模块</span>
              </div>
              <div class="record-body">
                <pre class="record-pre">${escapeHtml(editor.value.trim())}</pre>
              </div>
            </article>
          `;
          return;
        }
        structuredView.innerHTML = `<div class="summary"><span class="pill">模块：0</span></div><div class="empty">当前文件没有可拆分模块。可以切换到原文编辑查看内容。</div>`;
        return;
      }
      structuredView.innerHTML = `
        <div class="summary"><span class="pill">模块：${sections.length}</span></div>
        ${sortNewestFirst(sections.filter(section => matchSearch(section.raw) && matchTime(section.title))).map(section => `
          <article class="record">
            <div class="record-head">
              <div class="record-title">${escapeHtml(section.title)}</div>
              <span class="badge">模块</span>
            </div>
            <div class="record-body">
              <pre class="record-pre">${escapeHtml(section.body || section.raw)}</pre>
            </div>
          </article>
        `).join("")}
      `;
    }

    function renderMemory() {
      paginationBar.innerHTML = "";
      const blocks = parseTimeBlocks(editor.value);
      if (!blocks.length) {
        renderSections();
        return;
      }
      structuredView.innerHTML = `
        <div class="summary"><span class="pill">时间点：${blocks.length}</span></div>
        ${sortNewestFirst(blocks.filter(block => matchSearch(block.title + "\n" + block.body) && matchTime(block.title))).map(block => `
          <article class="record">
            <div class="record-head">
              <div class="record-title">${escapeHtml(block.title)}</div>
              <span class="badge">时间点</span>
            </div>
            <div class="record-body">
              <pre class="record-pre">${escapeHtml(block.body || "无正文")}</pre>
            </div>
          </article>
        `).join("")}
      `;
    }

    function renderCursor() {
      paginationBar.innerHTML = "";
      let data;
      try {
        data = JSON.parse(editor.value || "{}");
      } catch (err) {
        structuredView.innerHTML = `<div class="empty">JSON 解析失败：${escapeHtml(err.message)}。可以切换到原文编辑修正。</div>`;
        return;
      }
      structuredView.innerHTML = `
        <div class="summary"><span class="pill">JSON 字段：${Object.keys(data).length}</span></div>
        <article class="record">
          <div class="record-head">
            <div class="record-title">完整复盘游标</div>
            <span class="badge">JSON</span>
          </div>
          <div class="record-body">
            <pre class="record-pre">${escapeHtml(JSON.stringify(data, null, 2))}</pre>
          </div>
        </article>
      `;
    }

    function renderReport(title, rows) {
      paginationBar.innerHTML = "";
      structuredView.style.display = "block";
      editor.style.display = "none";
      saveBtn.style.display = "none";
      rawBtn.style.display = "inline-block";
      rawBtn.textContent = "返回当前文件";
      structuredView.innerHTML = `
        <div class="summary"><span class="pill">${escapeHtml(title)}</span></div>
        ${rows.map(row => `
          <article class="record">
            <div class="record-head">
              <div class="record-title">${escapeHtml(row.title)}</div>
              <span class="badge ${statusClass(row.status)}">${escapeHtml(row.status)}</span>
            </div>
            <div class="record-body"><pre class="record-pre">${escapeHtml(row.body || "")}</pre></div>
          </article>
        `).join("")}
      `;
    }

    async function showSelfCheck() {
      setStatus("正在执行自检...");
      const data = await api("/api/self-check");
      renderReport("安装自检报告", data.rows);
      setStatus("自检完成。", "ok");
    }

    async function showBackups() {
      if (!current) return;
      const data = await api(`/api/backups?id=${encodeURIComponent(current)}`);
      structuredView.style.display = "block";
      editor.style.display = "none";
      saveBtn.style.display = "none";
      rawBtn.style.display = "inline-block";
      rawBtn.textContent = "返回当前文件";
      structuredView.innerHTML = `
        <div class="summary"><span class="pill">备份：${data.backups.length}</span></div>
        ${data.backups.length ? data.backups.map(b => `
          <article class="record">
            <div class="record-head">
              <div class="record-title">${escapeHtml(b.name)}</div>
              <span class="badge">备份</span>
            </div>
            <div class="record-body">
              <div class="field"><div class="field-name">时间</div><div class="field-value">${escapeHtml(b.time)}</div></div>
              <div class="field"><div class="field-name">大小</div><div class="field-value">${escapeHtml(b.size)} bytes</div></div>
              <div class="field"><div class="field-name">路径</div><div class="field-value">${escapeHtml(b.path)}</div></div>
            </div>
            <div class="record-actions">
              <button class="danger" onclick="restoreBackup('${escapeHtml(b.name)}')">恢复这个备份</button>
            </div>
          </article>
        `).join("") : `<div class="empty">当前文件没有备份。</div>`}
      `;
      setStatus("已读取备份列表。", "ok");
    }

    async function restoreBackup(name) {
      if (!current) return;
      if (!confirm(`确定恢复备份“${name}”吗？当前文件会先自动备份，再被该备份覆盖。`)) return;
      await api("/api/restore", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: current, name })
      });
      rawMode = false;
      await loadFile();
      setStatus("已恢复备份。", "ok");
    }

    async function runArchive() {
      if (!confirm("确定执行归档？会先备份当前候选文件，并把已拒绝/已过期/已删除候选移入 archive。")) return;
      const data = await api("/api/archive", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      renderReport("归档结果", data.rows);
      if (current) {
        const refreshed = await api(`/api/file?id=${encodeURIComponent(current)}`);
        editor.value = refreshed.content;
        dirty = false;
      }
      setStatus("归档完成。", "ok");
    }

    async function showRuleCheck() {
      const data = await api("/api/rule-check");
      renderReport("规则冲突检查", data.rows);
      setStatus("规则冲突检查完成。", "ok");
    }

    async function showPathNavigator() {
      const data = await api("/api/paths");
      structuredView.style.display = "block";
      editor.style.display = "none";
      saveBtn.style.display = "none";
      rawBtn.style.display = "inline-block";
      rawBtn.textContent = "返回当前文件";
      structuredView.innerHTML = `
        <div class="summary"><span class="pill">路径导航：${data.paths.length}</span></div>
        ${data.paths.map(item => `
          <article class="record">
            <div class="record-head">
              <div class="record-title">${escapeHtml(item.title)}</div>
              <span class="badge">${escapeHtml(item.type)}</span>
            </div>
            <div class="record-body">
              <div class="field"><div class="field-name">说明</div><div class="field-value">${escapeHtml(item.description)}</div></div>
              <div class="field"><div class="field-name">路径</div><div class="field-value">${escapeHtml(item.path)}</div></div>
            </div>
            <div class="record-actions">
              <button onclick="openPath('${escapeHtml(item.id)}')">打开</button>
              <button onclick="copyPath('${escapeHtml(item.path)}')">复制路径</button>
            </div>
          </article>
        `).join("")}
      `;
      setStatus("已读取路径导航。", "ok");
    }

    async function openPath(id) {
      await api("/api/open-path", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id })
      });
      setStatus("已请求系统打开路径。", "ok");
    }

    async function copyPath(path) {
      await navigator.clipboard.writeText(path);
      setStatus("路径已复制。", "ok");
    }

    async function setRecordStatus(index, status) {
      const parsed = parseRecords(editor.value);
      const record = parsed.records[index];
      if (!record) return;
      const label = current === "candidates" ? "候选经验" : "待确认变更";
      if (!confirm(`确定把这条${label}标记为“${status}”吗？`)) return;
      const resultField = current === "candidates" ? "审查结论" : "处理结论";
      const statusField = current === "candidates" ? "状态" : "确认状态";
      let note = "";
      if (["已采纳", "已确认", "已拒绝", "已处理", "已过期", "已删除", "已归档"].includes(status)) {
        note = prompt("填写处理说明，可留空：", "") || "";
      }
      const updates = {};
      updates[statusField] = status;
      updates["处理时间"] = nowText();
      if (note) updates[resultField] = note;
      parsed.records[index].raw = updateRecordRaw(record, updates);
      editor.value = buildContent(parsed.prefix, parsed.records);
      dirty = true;
      renderStructured();
      await saveFile();
    }

    async function loadFile() {
      if (!current) return;
      const meta = files[current];
      fileTitle.textContent = meta.title;
      filePath.innerHTML = `<div class="desc">${escapeHtml(meta.description)}</div>`;
      editor.value = "";
      dirty = false;
      setStatus("正在读取...");
      try {
        const data = await api(`/api/file?id=${encodeURIComponent(current)}`);
        editor.value = data.content;
        renderStructured();
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
        renderStructured();
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
    rawBtn.onclick = () => {
      if (rawBtn.textContent === "返回当前文件") {
        rawMode = false;
        renderStructured();
        return;
      }
      rawMode = !rawMode;
      renderStructured();
    };
    searchInput.oninput = () => {
      searchText = searchInput.value;
      currentPage = 1;
      renderStructured();
    };
    timeFilterSelect.onchange = () => {
      timeFilter = timeFilterSelect.value;
      currentPage = 1;
      renderStructured();
    };
    async function init() {
      try {
        const data = await api("/api/files");
        files = data.files;
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

    def _path_items(self):
        items = [
            {
                "id": "maintenance_dir",
                "title": "维护目录",
                "type": "目录",
                "description": "复盘日志、候选经验、待确认变更、游标和归档内容的集中位置。",
                "path": str(self.server.root),
            },
            {
                "id": "automation_dir",
                "title": "自动化目录",
                "type": "目录",
                "description": "自动化配置、运行记忆和维护目录所在位置。",
                "path": str(self.server.codex_home / "automations" / "development-lesson-review"),
            },
            {
                "id": "automation_toml",
                "title": "自动化配置",
                "type": "文件",
                "description": "定时任务配置，包含执行时间、工作区和自动复盘 prompt。",
                "path": str(self.server.codex_home / "automations" / "development-lesson-review" / "automation.toml"),
            },
            {
                "id": "memory",
                "title": "自动化记忆",
                "type": "文件",
                "description": "人工可读的运行记忆和最近复盘结论。",
                "path": str(self.server.codex_home / "automations" / "development-lesson-review" / "memory.md"),
            },
            {
                "id": "review_checklist",
                "title": "执行清单",
                "type": "文件",
                "description": "每轮自动复盘的启动顺序、写入顺序和收尾检查。",
                "path": str(self.server.root / "review-checklist.md"),
            },
            {
                "id": "review_playbook",
                "title": "规则手册",
                "type": "文件",
                "description": "自动复盘的详细判断标准、持久层选择、候选和待确认规则。",
                "path": str(self.server.root / "review-playbook.md"),
            },
            {
                "id": "archive_dir",
                "title": "归档目录",
                "type": "目录",
                "description": "旧日志、旧候选和归档说明存放位置。",
                "path": str(self.server.root / "archive"),
            },
        ]
        for file_id, meta in FILES.items():
            if meta["path"] == "__AUTOMATION_MEMORY__":
                continue
            items.append({
                "id": f"file_{file_id}",
                "title": meta["title"],
                "type": "文件",
                "description": meta["description"],
                "path": str(self.server.root / meta["path"]),
            })
        return items

    def _allowed_open_paths(self):
        return {item["id"]: Path(item["path"]).resolve() for item in self._path_items()}

    def _backup_file(self, path):
        if path.exists():
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup = path.with_name(f"{path.name}.bak.{stamp}")
            shutil.copy2(path, backup)
            return backup
        return None

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _record_sections(self, content):
        marker = "\n## 记录"
        idx = content.find(marker)
        head_end = content.find("\n", idx + len(marker)) if idx >= 0 else -1
        prefix = content[:head_end + 1] if head_end >= 0 else content
        body = content[head_end + 1:] if head_end >= 0 else ""
        matches = list(re.finditer(r"^### .+$", body, re.MULTILINE))
        records = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            raw = body[start:end].strip()
            status_match = re.search(r"^- 状态[：:]\s*(.+)$", raw, re.MULTILINE)
            records.append({"raw": raw, "status": status_match.group(1).strip() if status_match else ""})
        return prefix, records

    def _record_month(self, raw):
        match = re.match(r"^###\s+(\d{4})-(\d{2})-", raw)
        if not match:
            return ""
        return f"{match.group(1)}-{match.group(2)}"

    def _self_check_rows(self):
        rows = []
        targets = [
            ("自动化配置", self.server.codex_home / "automations" / "development-lesson-review" / "automation.toml"),
            ("运行记忆", self.server.codex_home / "automations" / "development-lesson-review" / "memory.md"),
            ("维护面板", self.server.root / "start_dashboard.py"),
            ("复盘日志", self.server.root / "lesson-review-log.md"),
            ("候选经验", self.server.root / "lesson-review-candidates.md"),
            ("待确认变更", self.server.root / "lesson-review-pending-changes.md"),
            ("主游标", self.server.root / "lesson-review-cursor.json"),
        ]
        for title, path in targets:
            exists = path.exists()
            writable = os.access(path, os.W_OK) if exists else os.access(path.parent, os.W_OK)
            rows.append({
                "title": title,
                "status": "已通过" if exists and writable else "需处理",
                "body": f"路径：{path}\n存在：{exists}\n可写：{writable}",
            })
        try:
            cursor = json.loads((self.server.root / "lesson-review-cursor.json").read_text(encoding="utf-8"))
            rows.append({"title": "cursor JSON", "status": "已通过", "body": f"last_review_at：{cursor.get('last_review_at', '未填写')}"})
        except Exception as exc:
            rows.append({"title": "cursor JSON", "status": "需处理", "body": f"解析失败：{exc}"})
        return rows

    def _rule_check_rows(self):
        rows = []
        patterns = [
            "/Users/zonst/Documents/Codex/" + "lesson-review-maintenance",
            "/Users/zonst/.codex/vault/" + "lesson-review-maintenance",
            "memory.md " + "主游标",
            "主 " + "memory 游标",
            "可视化 " + "cursor",
        ]
        targets = [
            self.server.codex_home / "AGENTS.md",
            self.server.codex_home / "hooks" / "validation.md",
            self.server.codex_home / "vault" / "global-state.md",
            self.server.codex_home / "automations" / "development-lesson-review" / "automation.toml",
        ]
        for path in targets:
            if not path.exists():
                rows.append({"title": path.name, "status": "需处理", "body": f"文件不存在：{path}"})
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            hits = [p for p in patterns if p in text]
            rows.append({
                "title": str(path),
                "status": "需处理" if hits else "已通过",
                "body": "命中：\n" + "\n".join(hits) if hits else "未发现旧路径或旧 cursor 策略关键词。",
            })
        return rows

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
        if parsed.path == "/api/backups":
            path = self._file_path()
            if path is None:
                self._send(404, "未知文件", "text/plain; charset=utf-8")
                return
            backups = []
            for backup in sorted(path.parent.glob(f"{path.name}.bak.*"), reverse=True):
                stat = backup.stat()
                backups.append({
                    "name": backup.name,
                    "path": str(backup),
                    "size": stat.st_size,
                    "time": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                })
            self._json(200, {"backups": backups[:50]})
            return
        if parsed.path == "/api/self-check":
            self._json(200, {"rows": self._self_check_rows()})
            return
        if parsed.path == "/api/rule-check":
            self._json(200, {"rows": self._rule_check_rows()})
            return
        if parsed.path == "/api/paths":
            self._json(200, {"paths": self._path_items()})
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
        payload = self._read_json_body()
        content = payload.get("content", "")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._backup_file(path)
        path.write_text(content, encoding="utf-8")
        self._json(200, {"ok": True})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/restore":
            payload = self._read_json_body()
            file_id = payload.get("id", "")
            name = payload.get("name", "")
            if file_id not in FILES or not name:
                self._send(400, "参数错误", "text/plain; charset=utf-8")
                return
            old_path = self.path
            self.path = f"/api/file?id={file_id}"
            path = self._file_path()
            self.path = old_path
            if path is None:
                self._send(404, "未知文件", "text/plain; charset=utf-8")
                return
            backup = (path.parent / name).resolve()
            if not str(backup).startswith(str(path.parent.resolve())) or not backup.exists() or not backup.name.startswith(f"{path.name}.bak."):
                self._send(404, "未知备份", "text/plain; charset=utf-8")
                return
            self._backup_file(path)
            shutil.copy2(backup, path)
            self._json(200, {"ok": True})
            return
        if parsed.path == "/api/open-path":
            payload = self._read_json_body()
            path_id = payload.get("id", "")
            path = self._allowed_open_paths().get(path_id)
            if path is None:
                self._send(404, "未知路径", "text/plain; charset=utf-8")
                return
            if not path.exists():
                self._send(404, f"路径不存在：{path}", "text/plain; charset=utf-8")
                return
            subprocess.run(["open", str(path)], check=False)
            self._json(200, {"ok": True})
            return
        if parsed.path == "/api/archive":
            candidates = self.server.root / "lesson-review-candidates.md"
            log = self.server.root / "lesson-review-log.md"
            archive_dir = self.server.root / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            rows = []
            if candidates.exists():
                content = candidates.read_text(encoding="utf-8")
                prefix, records = self._record_sections(content)
                archive_status = {"已拒绝", "已过期", "已删除"}
                keep = [r["raw"] for r in records if r["status"] not in archive_status]
                move = [r["raw"] for r in records if r["status"] in archive_status]
                if move:
                    self._backup_file(candidates)
                    archive_file = archive_dir / f"lesson-review-candidates-{datetime.now().strftime('%Y-%m')}.md"
                    with archive_file.open("a", encoding="utf-8") as f:
                        f.write("\n\n## 自动归档 " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n\n")
                        f.write("\n\n".join(move))
                        f.write("\n")
                    candidates.write_text(prefix.rstrip() + "\n\n" + "\n\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
                    rows.append({"title": "候选经验归档", "status": "已通过", "body": f"已归档：{len(move)} 条\n保留：{len(keep)} 条\n归档文件：{archive_file}"})
                else:
                    rows.append({"title": "候选经验归档", "status": "已通过", "body": "没有需要归档的已拒绝、已过期或已删除候选。"})
            else:
                rows.append({"title": "候选经验归档", "status": "需处理", "body": "候选文件不存在。"})
            if log.exists():
                content = log.read_text(encoding="utf-8")
                prefix, records = self._record_sections(content)
                current_month = datetime.now().strftime("%Y-%m")
                keep = [r["raw"] for r in records if self._record_month(r["raw"]) in ("", current_month)]
                move = [r["raw"] for r in records if self._record_month(r["raw"]) not in ("", current_month)]
                if move:
                    self._backup_file(log)
                    archive_file = archive_dir / f"lesson-review-log-{datetime.now().strftime('%Y-%m')}.md"
                    with archive_file.open("a", encoding="utf-8") as f:
                        f.write("\n\n## 自动归档 " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n\n")
                        f.write("\n\n".join(move))
                        f.write("\n")
                    log.write_text(prefix.rstrip() + "\n\n" + "\n\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
                    rows.append({"title": "复盘日志归档", "status": "已通过", "body": f"已归档：{len(move)} 条\n保留：{len(keep)} 条\n归档文件：{archive_file}"})
                else:
                    rows.append({"title": "复盘日志归档", "status": "已通过", "body": "没有需要归档的非本月日志。"})
            else:
                rows.append({"title": "复盘日志归档", "status": "需处理", "body": "复盘日志不存在。"})
            self._json(200, {"rows": rows})
            return
        self._send(404, "未找到", "text/plain; charset=utf-8")

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
