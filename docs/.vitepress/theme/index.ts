import DefaultTheme from 'vitepress/theme'
import { useRouter, inBrowser } from 'vitepress'
import HomeCards from './HomeCards.vue'
import './style.css'

// 6 种页面切换动画
const ANIMS = ['bounce', 'spin', 'pop', 'slide-up', 'flip', 'jello']

// 记录最近 2 次用过的动画，确保相邻 3 次不重复
const recent: string[] = []

function pickAnim(): string {
  const pool = ANIMS.filter((a) => !recent.includes(a))
  const anim = pool[Math.floor(Math.random() * pool.length)]
  recent.push(anim)
  if (recent.length > 2) recent.shift()
  return anim
}

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.component('HomeCards', HomeCards)
  },
  setup() {
    if (!inBrowser) return
    if (!('startViewTransition' in document)) return

    const router = useRouter()

    // 拦截所有内部链接点击，随机选择一种动画
    document.addEventListener(
      'click',
      (e) => {
        const link = (e.target as Element)?.closest('a')
        if (!link) return
        const href = link.getAttribute('href')
        if (!href) return
        if (/^(https?:|\/\/|#|mailto:|tel:|javascript:)/.test(href)) return
        if (link.target || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return

        e.preventDefault()
        e.stopPropagation()

        const anim = pickAnim()
        document.documentElement.setAttribute('data-vt-anim', anim)

        document.startViewTransition(async () => {
          await router.go(href)
        })
      },
      { capture: true },
    )

    // 浏览器前进/后退也用随机动画（同样不重复）
    window.addEventListener('popstate', () => {
      const anim = pickAnim()
      document.documentElement.setAttribute('data-vt-anim', anim)
      document.startViewTransition(() => {})
    })
  },
}
