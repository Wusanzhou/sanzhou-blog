<script setup lang="ts">
const sections = [
  {
    emoji: '🚀',
    title: '入门指南',
    desc: '从零开始，掌握 AI 编程工具的核心用法。覆盖 Claude Code、Cursor、Copilot 等主流工具。',
    link: '/guide/',
    color: '#f59e0b',
    bg: '#fffbeb',
    border: '#fde68a',
  },
  {
    emoji: '🔨',
    title: '实战项目',
    desc: '真实项目驱动的学习记录，从需求分析到代码实现，全程 AI 辅助。',
    link: '/practice/',
    color: '#10b981',
    bg: '#ecfdf5',
    border: '#a7f3d0',
  },
  {
    emoji: '🛠️',
    title: '工具与效率',
    desc: '深入挖掘 AI 编程工具的高级技巧，提升日常开发效率。',
    link: '/tools/',
    color: '#6366f1',
    bg: '#eef2ff',
    border: '#c7d2fe',
  },
  {
    emoji: '🧠',
    title: '深入理解',
    desc: '理解 AI 编程背后的机制：Tool Use、Agent、Token 经济学、MCP 协议。',
    link: '/deep-dive/',
    color: '#ec4899',
    bg: '#fdf2f8',
    border: '#fbcfe8',
  },
  {
    emoji: '📝',
    title: '踩坑笔记',
    desc: '真实踩坑记录和排查过程，避免重蹈覆辙。每周 AI 编程周记。',
    link: '/notes/',
    color: '#f97316',
    bg: '#fff7ed',
    border: '#fed7aa',
  },
]
</script>

<template>
  <div class="home-cards">
    <p class="section-hint">📂 选择一个板块开始阅读</p>
    <div class="cards-grid">
      <a
        v-for="section in sections"
        :key="section.title"
        :href="section.link"
        class="card"
        :style="{
          '--card-bg': section.bg,
          '--card-border': section.border,
          '--card-color': section.color,
        }"
      >
        <span class="card-emoji">{{ section.emoji }}</span>
        <h2 class="card-title">{{ section.title }}</h2>
        <p class="card-desc">{{ section.desc }}</p>
        <span class="card-arrow">→</span>
      </a>
    </div>
  </div>
</template>

<style scoped>
.home-cards {
  max-width: 1152px;
  margin: 0 auto;
  padding: 64px 24px;
}

.section-hint {
  text-align: center;
  color: var(--vp-c-text-2);
  font-size: 14px;
  margin-bottom: 32px;
  letter-spacing: 1px;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 28px 24px 24px;
  border-radius: 16px;
  background: var(--card-bg);
  border: 1.5px solid var(--card-border);
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

.card-emoji {
  font-size: 36px;
  margin-bottom: 12px;
  display: block;
  line-height: 1;
}

.card-title {
  font-size: 17px;
  font-weight: 650;
  color: var(--vp-c-text-1);
  margin: 0 0 8px;
  letter-spacing: 0.3px;
}

.card-desc {
  font-size: 13px;
  color: var(--vp-c-text-2);
  line-height: 1.6;
  margin: 0 0 16px;
  flex: 1;
}

.card-arrow {
  font-size: 16px;
  color: var(--card-color);
  font-weight: 600;
  transition: transform 0.2s ease;
}

.card:hover .card-arrow {
  transform: translateX(4px);
}
</style>
