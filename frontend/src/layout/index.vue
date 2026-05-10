<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataAnalysis,
  DataLine,
  Document,
  HomeFilled,
  MagicStick,
  Setting,
  Operation,
  CreditCard
} from '@element-plus/icons-vue'

const route = useRoute()
const collapsed = ref(false)

const activeMenu = computed(() => route.meta?.activeMenu || route.path)

const menus = [
  { index: '/homepage', title: '系统首页', icon: HomeFilled },
  { index: '/ocr', title: 'OCR 控制台', icon: MagicStick },
  { index: '/receipts', title: '账单管理', icon: Document },
  { index: '/analytics/overview', title: '消费统计', icon: DataLine },
  { index: '/analytics/category', title: '分类分析', icon: DataAnalysis },
  {
    index: 'system-manage',
    title: '系统管理',
    icon: Setting,
    children: [
      { index: '/system/categories', title: '分类管理', icon: Operation },
      { index: '/system/payment-methods', title: '支付方式管理', icon: CreditCard }
    ]
  }
]
</script>

<template>
  <el-container class="app-shell">
    <el-aside class="app-aside" :width="collapsed ? '64px' : '232px'">
      <div class="brand" :class="{ collapsed }">
        <span class="brand-mark">SR</span>
        <span v-if="!collapsed" class="brand-text">SmartReceipts</span>
      </div>

      <el-menu
        class="side-menu"
        :collapse="collapsed"
        :default-active="activeMenu"
        router
        unique-opened
      >
        <template v-for="item in menus" :key="item.index">
          <el-tooltip
            v-if="!item.children"
            :content="item.title"
            :disabled="!collapsed"
            placement="right"
          >
            <el-menu-item :index="item.index" :title="item.title" class="menu-item">
              <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </el-tooltip>

          <el-sub-menu v-else :index="item.index" :title="item.title" popper-class="side-submenu-popper">
            <template #title>
              <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>

            <el-tooltip
              v-for="child in item.children"
              :key="child.index"
              :content="child.title"
              :disabled="!collapsed"
              placement="right"
            >
              <el-menu-item :index="child.index" :title="child.title" class="menu-item">
                <el-icon class="menu-icon child-icon"><component :is="child.icon" /></el-icon>
                <span>{{ child.title }}</span>
              </el-menu-item>
            </el-tooltip>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-button text class="collapse-btn" @click="collapsed = !collapsed">
            {{ collapsed ? '展开菜单' : '折叠菜单' }}
          </el-button>
          <span class="system-title">SmartReceipts 管理系统</span>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--sr-page-bg);
}

.app-aside {
  border-right: 1px solid var(--el-border-color-light);
  background: #ffffff;
  transition: width 0.2s ease;
}

.brand {
  height: 60px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.brand.collapsed {
  justify-content: center;
  padding: 0;
}

.brand-mark {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--el-color-primary);
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.brand-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.side-menu {
  border-right: none;
  padding: 10px 0 16px;
}

.menu-item {
  --el-menu-item-height: 46px;
}

.menu-icon {
  font-size: 18px;
}

.child-icon {
  font-size: 16px;
}

.app-header {
  height: 60px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: #ffffff;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  padding: 0 6px;
}

.system-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.app-main {
  padding: 20px;
  overflow-x: hidden;
}

@media (max-width: 960px) {
  .app-main {
    padding: 14px;
  }

  .system-title {
    font-size: 14px;
  }
}
</style>