# 用 AI 搭建个人博客

> 这篇记录我第一次用 Claude Code 和 VitePress 搭建这个博客的过程。

## 项目背景

一直想有个地方记录自己的 AI 编程学习过程。传统的博客框架要么太重（WordPress），要么需要手动配置很多东西（Hexo、Hugo）。这次我决定**完全用 AI 来帮我搭建**，从零到上线，只给方向，让 AI 来写代码。

## 技术选型

我把需求告诉 AI：「想建一个个人技术博客，部署到 GitHub Pages，主要用于记录 AI 编程学习。」

AI 给出了几个方案：

| 方案 | 评价 |
|------|------|
| VitePress | ✅ AI 推荐，基于 Vue + Vite，Markdown 写作，天然支持 GitHub Pages |
| Hexo | 主题多，但配置稍繁琐 |
| Hugo | 构建快，但需要额外安装 Go 环境 |
| Next.js + MDX | 最灵活但太重，不适合纯博客 |

最终选了 **VitePress**。理由很简单：我 Node.js 环境现成的，VitePress 配置简单，默认主题就很好看。

## 项目结构

AI 帮我设计的目录结构：

```
sanzhou-blog/
├── .github/workflows/    # 自动部署配置
├── docs/                 # 所有内容都在这里
│   ├── .vitepress/       # VitePress 配置
│   ├── guide/            # 学习路线
│   ├── practice/         # 练习项目
│   ├── tools/            # 工具笔记
│   ├── deep-dive/        # 理解笔记
│   └── notes/            # 问题记录
└── package.json
```

## 实现过程

### 1. 初始化项目

整个初始化我一句话都没写，AI 帮我完成了：

- `npm init` + 安装 VitePress
- 创建所有目录和配置文件
- 设置导航栏、侧边栏
- 写好每个板块的占位页面

这大概花了 **不到 5 分钟**。

### 2. 配置 VitePress

VitePress 的配置集中在 `docs/.vitepress/config.ts`。AI 帮我配置了：

- **导航栏**：6 个一级入口
- **侧边栏**：每个板块独立的文章列表
- **搜索**：本地全文搜索
- **中文本地化**：页面导航、大纲等全部中文化
- **GitHub 编辑链接**：每篇页面可以直接跳转 GitHub 编辑

::: tip 一点心得
VitePress 的配置文件本身也是 TypeScript，有类型提示，配合 AI 写起来非常快。AI 能记住所有配置项，不需要去翻文档。
:::

### 3. 部署到 GitHub Pages

AI 帮我写好了 GitHub Actions 工作流：

```yaml
# .github/workflows/deploy.yml
# 每次 push 到 main 分支时自动构建并部署
```

原理很简单：
1. checkout 代码
2. `npm ci && npm run build` 构建静态文件
3. 部署到 `gh-pages` 分支
4. GitHub Pages 自动从 `gh-pages` 分支读取并发布

### 4. 写第一篇文章

也就是你正在读的这篇。整个过程是这样的：

1. 我告诉 AI 博客大纲和板块设置
2. AI 提出详细的文章结构
3. 我确认后，AI 一次性生成了整篇文章
4. 我 review 并调整了细节

## 踩坑记录

### 坑 1：VitePress 的 base 路径

如果 GitHub Pages 部署在 `<username>.github.io/<repo>/`，需要在 config 中设置 `base: '/<repo>/'`。

但如果你用自定义域名，或者 repo 名是 `<username>.github.io`，就不需要。我这边需要确认一下最终的 URL 再调整。

### 坑 2：Node.js 版本

GitHub Actions 中的 Node 版本要和本地一致，否则可能构建失败。我在 workflow 中指定了 Node 18。

## 复盘总结

### AI 做得好的地方

- **项目初始化极快**：从零到可运行的博客框架，不到 5 分钟
- **配置完整**：导航、侧边栏、搜索、中文化，全部覆盖
- **代码规范**：TypeScript 配置、合理的目录结构

### 需要人工判断的地方

- **博客名称和定位**：AI 只是执行者，名字「三舟」、主题「AI 编程」需要我自己想
- **内容大纲**：AI 能建议大纲，但哪些板块重要、哪些砍掉，需要我根据自身情况决策
- **文章质量把关**：AI 写的文章需要我 review，确保内容准确、表述自然

### 整体感受

用 AI 搭博客的效率是传统方式的 **10 倍以上**。以前要花一晚上研究文档、配置、调试，现在只要把想法说清楚，AI 几分钟搞定。

---

> 后面准备记录：[AI 生成单元测试](/practice/ai-unit-tests) — 我尝试让 AI 补测试的过程

---

*最后更新：2026-06-07*
