---
layout: home

hero:
  name: "三舟的编程笔记"
  text: "AI 编程学习记录"
  tagline: 记录我学习 AI 协作编程的过程
  actions:
    - theme: brand
      text: 看最近记录
      link: /guide/
    - theme: alt
      text: 关于我
      link: /about
---

<HomeCards />

## 最近更新

<div class="recent-posts">

- **2026-06-07** — [用 AI 搭建个人博客](/practice/build-blog-with-ai)  
  <span class="post-desc">记录我用 Claude Code 和 VitePress 搭这个博客时做了什么、遇到什么问题。</span>

</div>

<style>
.recent-posts {
  max-width: 640px;
  margin: 24px auto;
  padding: 0 24px;
}
.recent-posts p {
  margin: 12px 0;
  line-height: 1.8;
}
.post-desc {
  color: var(--vp-c-text-2);
  font-size: 13px;
}
</style>
