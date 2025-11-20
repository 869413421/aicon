import { createRouter, createWebHistory } from 'vue-router'
import { setupAuthGuard } from './guards'

// 布局组件
const AuthLayout = () => import('@/components/layout/AuthLayout.vue')
const MainLayout = () => import('@/components/layout/MainLayout.vue')

// 页面组件
const Login = () => import('@/views/Login.vue')
const Register = () => import('@/views/Register.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const Projects = () => import('@/views/Projects.vue')
const ProjectDetail = () => import('@/components/project/ProjectDetail.vue')
const ChapterManagement = () => import('@/views/chapters/ChapterManagement.vue')
const GenerationQueue = () => import('@/views/GenerationQueue.vue')
const GenerationSettings = () => import('@/views/GenerationSettings.vue')
const Publish = () => import('@/views/Publish.vue')
const Settings = () => import('@/views/Settings.vue')

const routes = [
  {
    path: '/',
    name: 'Home',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: AuthLayout,
    meta: { requiresGuest: true },
    children: [
      {
        path: '',
        name: 'LoginPage',
        component: Login,
        props: {
          title: '欢迎回来',
          subtitle: '登录您的账户继续使用AI内容生成平台'
        }
      }
    ]
  },
  {
    path: '/register',
    name: 'Register',
    component: AuthLayout,
    meta: { requiresGuest: true },
    children: [
      {
        path: '',
        name: 'RegisterPage',
        component: Register,
        props: {
          title: '创建账户',
          subtitle: '加入AICG平台，开始您的AI内容创作之旅'
        }
      }
    ]
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'DashboardPage',
        component: Dashboard
      }
    ]
  },
  {
    path: '/projects',
    name: 'Projects',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'ProjectsPage',
        component: Projects
      },
      {
        path: ':projectId',
        name: 'ProjectDetail',
        component: ProjectDetail,
        props: true
      },
      {
        path: ':projectId/chapters',
        name: 'ChapterManagement',
        component: ChapterManagement,
        props: true
      },
      {
        path: ':projectId/chapters/:chapterId/paragraphs',
        name: 'ParagraphManagement',
        component: () => import('@/views/chapters/ParagraphManagement.vue'),
        props: true
      }
    ]
  },
  {
    path: '/generation',
    name: 'Generation',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'GenerationPage',
        component: GenerationQueue
      }
    ]
  },
  {
    path: '/generation/settings',
    name: 'GenerationSettings',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'GenerationSettingsPage',
        component: GenerationSettings
      }
    ]
  },
  {
    path: '/publish',
    name: 'Publish',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'PublishPage',
        component: Publish
      }
    ]
  },
  {
    path: '/settings',
    name: 'Settings',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'SettingsPage',
        component: Settings
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 设置路由守卫
setupAuthGuard(router)

export default router