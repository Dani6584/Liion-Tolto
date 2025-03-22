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
    {
      path: '/OCR',
      name: 'ocr',
      component: () => import('@/views/OCR.vue'),
    },
    {
      path: '/data/:id',
      name: 'data2', 
      component: () => import('@/components/Content.vue'),
    },
    {
      path: '/history',
      name: 'history',
      component: () => import('@/components/Lista.vue'),
    }
  ],
})

export default router