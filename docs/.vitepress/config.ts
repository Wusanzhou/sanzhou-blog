import { defineConfig } from 'vitepress'

// 导航栏
const nav = [
  { text: '首页', link: '/' },
  { text: '入门指南', link: '/guide/' },
  { text: '实战项目', link: '/practice/' },
  { text: '工具效率', link: '/tools/' },
  { text: '深入理解', link: '/deep-dive/' },
  { text: '踩坑笔记', link: '/notes/' },
  { text: '关于', link: '/about' },
]

// 侧边栏
const sidebar = {
  '/guide/': [
    {
      text: '🚀 入门指南',
      items: [
        { text: '概述', link: '/guide/' },
        { text: 'AI 编程工具概览', link: '/guide/tools-overview' },
        { text: 'Prompt Engineering 入门', link: '/guide/prompt-engineering' },
        { text: '从零搭建第一个 AI 辅助项目', link: '/guide/first-project' },
        { text: 'Context 管理技巧', link: '/guide/context-management' },
        { text: 'Git 与 AI 协作工作流', link: '/guide/git-ai-workflow' },
      ],
    },
  ],
  '/practice/': [
    {
      text: '🔨 实战项目',
      items: [
        { text: '概述', link: '/practice/' },
        { text: '用 AI 搭建个人博客', link: '/practice/build-blog-with-ai' },
        { text: 'AI 生成单元测试', link: '/practice/ai-unit-tests' },
        { text: 'AI 辅助重构老旧代码', link: '/practice/ai-refactoring' },
        { text: '用 AI 写全栈应用', link: '/practice/ai-fullstack' },
        { text: 'AI + API 集成实战', link: '/practice/ai-api-integration' },
      ],
    },
  ],
  '/tools/': [
    {
      text: '🛠️ 工具与效率',
      items: [
        { text: '概述', link: '/tools/' },
        { text: 'Claude Code 深度使用技巧', link: '/tools/claude-code-tips' },
        { text: 'Cursor Rules 系统详解', link: '/tools/cursor-rules' },
        { text: 'VSCode + AI 插件组合', link: '/tools/vscode-ai-plugins' },
        { text: 'Shell 别名与 AI 辅助', link: '/tools/shell-ai' },
        { text: '多模型协作策略', link: '/tools/multi-model' },
      ],
    },
  ],
  '/deep-dive/': [
    {
      text: '🧠 深入理解',
      items: [
        { text: '概述', link: '/deep-dive/' },
        { text: 'Tool Use 机制解析', link: '/deep-dive/tool-use' },
        { text: 'Agent 架构设计', link: '/deep-dive/agent-architecture' },
        { text: 'Context Window 与 Token 经济', link: '/deep-dive/token-economics' },
        { text: 'MCP 协议入门', link: '/deep-dive/mcp-protocol' },
        { text: 'Prompt Cache 原理与实战', link: '/deep-dive/prompt-cache' },
      ],
    },
  ],
  '/notes/': [
    {
      text: '📝 踩坑笔记',
      items: [
        { text: '全部笔记', link: '/notes/' },
        { text: '博客搭建全记录', link: '/notes/building-sanzhou-blog' },
        { text: 'AI 编程周记', link: '/notes/weekly' },
      ],
    },
  ],
}

export default defineConfig({
  title: '三舟的编程笔记',
  description: 'AI 编程学习记录与思考',
  lang: 'zh-CN',
  base: '/sanzhou-blog/',

  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
  ],

  themeConfig: {
    nav,
    sidebar,

    // 编辑链接
    editLink: {
      pattern: 'https://github.com/zonst/sanzhou-blog/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页',
    },

    // 页脚
    footer: {
      message: '用 AI 辅助编写 · 持续学习记录',
      copyright: '© 2026 三舟',
    },

    // 搜索
    search: {
      provider: 'local',
    },

    // 社交链接
    socialLinks: [
      { icon: 'github', link: 'https://github.com/zonst' },
    ],

    // 文档元数据
    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },

    // 大纲
    outline: {
      label: '页面导航',
      level: [2, 3],
    },

    lastUpdated: {
      text: '最后更新于',
    },
  },

  // 忽略死链（未来文章占位）
  ignoreDeadLinks: true,

  // Markdown 配置
  markdown: {
    lineNumbers: true,
  },
})
