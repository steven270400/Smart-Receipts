import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import OcrConsole from '../views/OcrConsole.vue'
import ReceiptManage from '../views/ReceiptManage.vue'
import ConsumptionStats from '../views/ConsumptionStats.vue'
import CategoryAnalysis from '../views/CategoryAnalysis.vue'
import CategoryManage from '../views/CategoryManage.vue'
import PaymentMethodManage from '../views/PaymentMethodManage.vue'
import { addOperationLog } from '../stores/operationLog'

const routes = [
  {
    path: '/',
    redirect: '/homepage'
  },
  {
    path: '/dashboard',
    redirect: '/homepage'
  },
  {
    path: '/homepage',
    name: 'Homepage',
    component: Dashboard,
    meta: {
      activeMenu: '/homepage'
    }
  },
  {
    path: '/ocr',
    name: 'OcrConsole',
    component: OcrConsole,
    meta: {
      activeMenu: '/ocr'
    }
  },
  {
    path: '/receipts',
    name: 'ReceiptManage',
    component: ReceiptManage,
    meta: {
      activeMenu: '/receipts'
    }
  },
  {
    path: '/analytics/overview',
    name: 'AnalyticsOverview',
    component: ConsumptionStats,
    meta: {
      activeMenu: '/analytics/overview'
    }
  },
  {
    path: '/analytics/category',
    name: 'AnalyticsCategory',
    component: CategoryAnalysis,
    meta: {
      activeMenu: '/analytics/category'
    }
  },
  {
    path: '/system/categories',
    name: 'CategoryManage',
    component: CategoryManage,
    meta: {
      activeMenu: '/system/categories'
    }
  },
  {
    path: '/system/payment-methods',
    name: 'PaymentMethodManage',
    component: PaymentMethodManage,
    meta: {
      activeMenu: '/system/payment-methods'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const routeLabelMap = {
  '/homepage': '系统首页',
  '/ocr': 'OCR 控制台',
  '/receipts': '账单管理',
  '/analytics/overview': '消费统计',
  '/analytics/category': '分类分析',
  '/system/categories': '分类管理',
  '/system/payment-methods': '支付方式管理'
}

router.afterEach((to, from) => {
  if (to.fullPath === from.fullPath) {
    return
  }
  const label = routeLabelMap[to.path] || to.path
  addOperationLog('info', `用户进入页面：${label}`)
})

export default router
