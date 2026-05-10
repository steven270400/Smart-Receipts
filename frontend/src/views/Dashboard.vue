<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import PageContainer from '../components/PageContainer.vue'
import LogPanel from '../components/dashboard/LogPanel.vue'
import { useAnalyticsData } from '../composables/useAnalyticsData'
import { addOperationLog, clearOperationLogs, useOperationLogStore } from '../stores/operationLog'
import { useReceiptEventStore } from '../stores/receiptEvents'

const router = useRouter()
const loading = ref(false)

const { state, load } = useAnalyticsData()
const logStore = useOperationLogStore()
const receiptEvents = useReceiptEventStore()
const initialized = ref(false)
const logs = computed(() => logStore.logs)

const overviewCards = [
  { key: 'totalReceipts', label: '总账单数', suffix: '条' },
  { key: 'todayReceipts', label: '今日识别数（代理）', suffix: '条' },
  { key: 'categoryCount', label: '分类总数', suffix: '个' },
  { key: 'paymentMethodCount', label: '支付方式总数', suffix: '个' }
]

const quickLinks = [
  { label: '前往 OCR 控制台', path: '/ocr', type: 'primary' },
  { label: '前往账单管理', path: '/receipts', type: '' },
  { label: '查看消费统计', path: '/analytics/overview', type: '' },
  { label: '查看分类分析', path: '/analytics/category', type: '' }
]

const features = [
  {
    title: 'OCR 票据识别',
    desc: '支持票据图片上传、文本识别与结构化字段抽取。'
  },
  {
    title: '账单管理',
    desc: '支持账单筛选、分页、新增、编辑、删除等基础管理能力。'
  },
  {
    title: '消费统计',
    desc: '提供消费总览、趋势分析、近期消费与 Top 消费洞察。'
  },
  {
    title: '分类分析',
    desc: '聚焦消费结构，展示分类占比、分类金额排行与笔数统计。'
  },
  {
    title: '系统管理',
    desc: '提供分类与支付方式的只读聚合管理视图。'
  }
]

async function initialize() {
  loading.value = true
  try {
    await load()
    addOperationLog('success', '系统首页数据加载完成')
  } catch (error) {
    addOperationLog('error', `系统首页数据加载失败: ${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    loading.value = false
  }
}

async function onRefresh() {
  addOperationLog('warning', '用户触发首页数据刷新')
  await initialize()
}

function onClearLogs() {
  clearOperationLogs()
  addOperationLog('success', '日志已清空')
}

function onQuickLinkClick(link) {
  addOperationLog('info', `用户点击快捷入口：${link.label}`)
  router.push(link.path)
}

watch(
  () => receiptEvents.version,
  async () => {
    if (!initialized.value) {
      return
    }
    await initialize()
  }
)

onMounted(async () => {
  await initialize()
  initialized.value = true
})
</script>

<template>
  <PageContainer title="系统首页" subtitle="系统入口与运行状态概览">
    <el-card shadow="never" class="sr-card welcome-card">
      <div class="welcome-title">欢迎使用 SmartReceipts 管理系统</div>
      <div class="welcome-desc">
        在一个页面集中查看系统运行状态，并快速进入 OCR、账单与分析模块。
      </div>
    </el-card>

    <el-row :gutter="16">
      <el-col v-for="item in overviewCards" :key="item.key" :xs="24" :sm="12" :lg="6">
        <el-card shadow="never" class="sr-card overview-card" v-loading="loading">
          <div class="overview-label">{{ item.label }}</div>
          <div class="overview-value">{{ state.overview[item.key] || 0 }} {{ item.suffix }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="6">
        <el-card shadow="never" class="sr-card card-fill">
          <template #header>
            <div class="sr-card-header">快捷入口</div>
          </template>
          <div class="quick-grid">
            <el-button
              v-for="link in quickLinks"
              :key="link.path"
              :type="link.type"
              class="quick-link-btn"
              @click="onQuickLinkClick(link)"
            >
              {{ link.label }}
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="18">
        <el-card shadow="never" class="sr-card card-fill">
          <template #header>
            <div class="sr-card-header">系统功能介绍</div>
          </template>
          <div class="feature-grid">
            <div v-for="item in features" :key="item.title" class="feature-item">
              <div class="feature-title">{{ item.title }}</div>
              <div class="feature-desc">{{ item.desc }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <LogPanel :logs="logs" :loading="loading" @refresh="onRefresh" @clear="onClearLogs" />
  </PageContainer>
</template>

<style scoped>
.welcome-card {
  border: none;
  background: linear-gradient(135deg, #ecf5ff 0%, #f7faff 100%);
}

.welcome-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.welcome-desc {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
}

.overview-card {
  height: 100%;
}

.overview-label {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.overview-value {
  margin-top: 8px;
  font-size: 26px;
  font-weight: 700;
  color: var(--el-text-color-primary);
}

.card-fill {
  height: 100%;
}

.quick-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  max-width: 260px;
}

.quick-link-btn {
  justify-content: flex-start;
  width: 100%;
  min-height: 40px;
}

.feature-grid {
  display: grid;
  gap: 10px;
}

.feature-item {
  display: grid;
  grid-template-columns: 140px 1fr;
  align-items: flex-start;
  column-gap: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 11px 12px;
  background: #fafcff;
}

.feature-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.feature-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .feature-item {
    grid-template-columns: 1fr;
    row-gap: 4px;
  }
}
</style>
