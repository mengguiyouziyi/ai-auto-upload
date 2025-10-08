import { createRouter, createWebHashHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import AccountManagement from '../views/AccountManagement.vue'
import MaterialManagement from '../views/MaterialManagement.vue'
import PublishCenter from '../views/PublishCenter.vue'
import About from '../views/About.vue'

// AI功能页面
import AIWorkbench from '../views/AIWorkbench.vue'
import TextOptimize from '../views/TextOptimize.vue'
import VideoGenerate from '../views/VideoGenerate.vue'
import AudioGenerate from '../views/AudioGenerate.vue'
import SpiderTool from '../views/SpiderTool.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/ai-workbench',
    name: 'AIWorkbench',
    component: AIWorkbench
  },
  {
    path: '/text-optimize',
    name: 'TextOptimize',
    component: TextOptimize
  },
  {
    path: '/video-generate',
    name: 'VideoGenerate',
    component: VideoGenerate
  },
  {
    path: '/audio-generate',
    name: 'AudioGenerate',
    component: AudioGenerate
  },
  {
    path: '/spider-tool',
    name: 'SpiderTool',
    component: SpiderTool
  },
  {
    path: '/account-management',
    name: 'AccountManagement',
    component: AccountManagement
  },
  {
    path: '/material-management',
    name: 'MaterialManagement',
    component: MaterialManagement
  },
  {
    path: '/publish-center',
    name: 'PublishCenter',
    component: PublishCenter
  },
  {
    path: '/about',
    name: 'About',
    component: About
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router