# 三舟的编程笔记

我把自己学习 AI 编程、折腾工具、做小项目时的记录放在这里。这里不是教程站，更像一本公开的学习笔记。站点用 VitePress 写，GitHub Pages 自动部署。

## 本地开发

```bash
npm install
npm run dev
```

## 构建

```bash
npm run build
npm run preview  # 预览构建结果
```

## 内容结构

仓库里主要放三类东西：

- `docs/`：博客正文，VitePress 从这里构建站点。
- `tools/`：独立工具、脚本和安装包，不参与博客构建。
- `.github/workflows/`：GitHub Actions 部署配置。

博客正文目录现在先这样分：

- `docs/guide/`：学习路线和基础概念
- `docs/practice/`：我做过的练习项目
- `docs/tools/`：工具使用笔记
- `docs/deep-dive/`：理解过程和原理笔记
- `docs/notes/`：日常问题和踩坑记录

工具目录：

- `tools/development-lesson-review/`：Codex 定时复盘任务安装包。

## 目录约定

- 写学习记录，放在 `docs/`。
- 更新站点配置时，改 `docs/.vitepress/`。
- 更新 GitHub Pages 部署流程，改 `.github/workflows/`。
- 独立工具放到 `tools/工具名/`，工具自己的说明写在对应目录里。
- 不提交 `node_modules/`、构建产物、IDE 配置、真实密钥、本机日志或备份文件。

## 技术栈

- [VitePress](https://vitepress.dev/) — 静态站点生成器
- [GitHub Pages](https://pages.github.com/) — 托管与部署
- [GitHub Actions](https://github.com/features/actions) — 自动构建部署
