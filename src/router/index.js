import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path:"/",
      name:"home"
    },
    {
      path: '/data',
      name: 'data',
      component: () => import('@/components/Content.vue'),
    },
  ],
})

export default router