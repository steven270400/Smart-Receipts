import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import OcrConsole from '../views/OcrConsole.vue'
import ReceiptManage from '../views/ReceiptManage.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/ocr',
    name: 'OcrConsole',
    component: OcrConsole
  },
  {
    path: '/receipts',
    name: 'ReceiptManage',
    component: ReceiptManage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router