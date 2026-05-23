// 路由配置：统一管理首页与三个维度页面的懒加载入口。
import { createRouter, createWebHashHistory } from 'vue-router'

// 页面路由表：每个页面额外携带浏览器标题。
const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/pages/home/HomePage.vue'),
    meta: { title: 'Visualizing Potential Well' }
  },
  {
    path: '/1',
    name: '1d',
    component: () => import('@/pages/1d/InfiniteWell1DPage.vue'),
    meta: { title: '1D Potential Well' }
  },
  {
    path: '/2',
    name: '2d',
    component: () => import('@/pages/2d/InfiniteWell2DPage.vue'),
    meta: { title: '2D Potential Well' }
  },
  {
    path: '/3',
    name: '3d',
    component: () => import('@/pages/3d/InfiniteWell3DPage.vue'),
    meta: { title: '3D Potential Well' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由切换后同步更新浏览器标题，避免每个页面重复处理。
router.afterEach((to) => {
  const title = to.meta?.title
  if (title) {
    document.title = title
  }
})

export default router
