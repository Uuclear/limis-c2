import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台' },
      },
      {
        path: 'projects',
        name: 'ProjectList',
        component: () => import('@/views/project/index.vue'),
        meta: { title: '项目管理' },
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/project/detail.vue'),
        meta: { title: '项目详情' },
      },
      {
        path: 'commissions',
        name: 'CommissionList',
        component: () => import('@/views/commission/index.vue'),
        meta: { title: '委托管理' },
      },
      {
        path: 'commissions/:id',
        name: 'CommissionDetail',
        component: () => import('@/views/commission/detail.vue'),
        meta: { title: '委托详情' },
      },
      {
        path: 'samples',
        name: 'SampleList',
        component: () => import('@/views/sample/index.vue'),
        meta: { title: '样品管理' },
      },
      {
        path: 'samples/:id',
        name: 'SampleDetail',
        component: () => import('@/views/sample/detail.vue'),
        meta: { title: '样品详情' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = getToken()
  if (to.meta.public) {
    if (token && to.name === 'Login') {
      next({ path: '/dashboard' })
    } else {
      next()
    }
  } else {
    if (!token) {
      next({ path: '/login', query: { redirect: to.fullPath } })
    } else {
      next()
    }
  }
})

export default router
