<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import SummaryCards from '../components/dashboard/SummaryCards.vue'
import CategoryPieChart from '../components/dashboard/CategoryPieChart.vue'
import MonthlyTrendChart from '../components/dashboard/MonthlyTrendChart.vue'
import TopExpenseList from '../components/dashboard/TopExpenseList.vue'
import LogPanel from '../components/dashboard/LogPanel.vue'
import { toDateString, toDateTimeString } from '../utils/date'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const pageText = {
  title: '智能票据识别与消费管理系统',
  subtitle: 'Dashboard 首页',
  goOcr: '前往 OCR 控制台',
  goReceiptManage: '前往账单管理',
  logInitDone: 'Dashboard 页面初始化完成',
  logSummaryLoaded: '已加载近30天概览数据',
  logCategoryLoaded: '已加载近30天分类饼图数据',
  logTrendLoaded: '已加载近6个月趋势数据',
  logTopLoaded: '已加载近6个月最大消费记录数据',
  logRefresh: '用户触发数据刷新',
  logCleared: '日志已清空',
  logPieRendered: '分类饼图渲染完成',
  logLineRendered: '月趋势折线图渲染完成',
  logLoadError: 'Dashboard 数据加载失败'
}

const router = useRouter()
const loading = ref(false)
let nextLogId = 1000

const state = reactive({
  summary: {
    last30DaysTotal: 0,
    last30DaysCount: 0,
    topCategory: '',
    topCategoryAmount: 0,
    maxExpenseAmount: 0
  },
  categoryData: [],
  monthlyTrendData: [],
  topExpenses: [],
  logs: []
})

function formatNow() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

function monthKey(value) {
  const pad = (v) => String(v).padStart(2, '0')
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}`
}

function monthLabel(value) {
  const [year, month] = String(value || '').split('-')
  if (!year || !month) {
    return String(value || '')
  }
  return `${year}年${month}月`
}

function round2(value) {
  return Number(Number(value || 0).toFixed(2))
}

function parseDate(value) {
  if (!value) {
    return null
  }
  const text = String(value).replace(/-/g, '/')
  const date = new Date(text)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  return date
}

function addLog(level, message) {
  state.logs.unshift({
    id: nextLogId++,
    time: formatNow(),
    level,
    message
  })
}

async function request(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }
  const payload = await response.json()
  if (payload.code !== 0) {
    throw new Error(payload.message || 'Request failed')
  }
  return payload.data
}

async function fetchReceipts(params) {
  const query = new URLSearchParams()
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') {
      return
    }
    query.append(key, String(value))
  })

  const suffix = query.toString() ? `?${query.toString()}` : ''
  return request(`${API_BASE_URL}/receipts${suffix}`)
}

function buildSummaryAndCategory(last30List) {
  const total = last30List.reduce((acc, item) => acc + Number(item.amount || 0), 0)
  const categoryMap = {}

  for (const item of last30List) {
    const key = item.category || '其他'
    categoryMap[key] = (categoryMap[key] || 0) + Number(item.amount || 0)
  }

  const categoryData = Object.entries(categoryMap)
    .map(([category, amount]) => ({ category, amount: round2(amount) }))
    .sort((a, b) => b.amount - a.amount)

  const topCategory = categoryData[0] || { category: '', amount: 0 }

  state.summary.last30DaysTotal = round2(total)
  state.summary.last30DaysCount = last30List.length
  state.summary.topCategory = topCategory.category
  state.summary.topCategoryAmount = round2(topCategory.amount)
  state.categoryData = categoryData
}

function buildMonthlyTrend(last6MonthsList) {
  const now = new Date()
  const months = []
  for (let i = 5; i >= 0; i -= 1) {
    const d = new Date(now)
    d.setDate(1)
    d.setMonth(d.getMonth() - i)
    months.push(monthKey(d))
  }

  const trendMap = {}
  for (const month of months) {
    trendMap[month] = 0
  }

  for (const item of last6MonthsList) {
    const time = parseDate(item.transaction_time)
    if (!time) {
      continue
    }
    const key = monthKey(time)
    if (Object.prototype.hasOwnProperty.call(trendMap, key)) {
      trendMap[key] += Number(item.amount || 0)
    }
  }

  state.monthlyTrendData = months.map((month) => ({
    month,
    monthLabel: monthLabel(month),
    amount: round2(trendMap[month])
  }))
}

function buildTopExpenses(last6MonthsList) {
  const sorted = [...last6MonthsList]
    .sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
    .slice(0, 5)

  state.topExpenses = sorted.map((item) => ({
    id: item.id,
    merchant: item.merchant,
    amount: round2(item.amount),
    category: item.category || '其他',
    date: toDateString(item.transaction_time)
  }))

  state.summary.maxExpenseAmount = round2(state.topExpenses[0]?.amount || 0)
}

async function loadDashboardData() {
  loading.value = true

  try {
    const now = new Date()

    const start30 = new Date(now)
    start30.setDate(start30.getDate() - 30)

    const start6mTrend = new Date(now)
    start6mTrend.setMonth(start6mTrend.getMonth() - 6)

    const start6m = new Date(now)
    start6m.setMonth(start6m.getMonth() - 6)

    const payload = await fetchReceipts({
      page: 1,
      size: 1000,
      start_time: toDateTimeString(start6m),
      end_time: toDateTimeString(now)
    })

    const allRows = payload.list || []

    const rowsWithTime = allRows.filter((item) => parseDate(item.transaction_time))

    const last30Rows = rowsWithTime.filter((item) => {
      const t = parseDate(item.transaction_time)
      return t && t >= start30
    })

    const last6mTrendRows = rowsWithTime.filter((item) => {
      const t = parseDate(item.transaction_time)
      return t && t >= start6mTrend
    })

    buildSummaryAndCategory(last30Rows)
    addLog('info', pageText.logSummaryLoaded)
    addLog('info', pageText.logCategoryLoaded)

    buildMonthlyTrend(last6mTrendRows)
    addLog('info', pageText.logTrendLoaded)

    buildTopExpenses(rowsWithTime)
    addLog('info', pageText.logTopLoaded)

    addLog('success', pageText.logInitDone)
  } catch (error) {
    addLog('error', `${pageText.logLoadError}: ${error instanceof Error ? error.message : 'Unknown error'}`)
  } finally {
    loading.value = false
  }
}

async function initialize() {
  state.logs = []
  await loadDashboardData()
}

async function onRefresh() {
  addLog('warning', pageText.logRefresh)
  await loadDashboardData()
}

function onClearLogs() {
  state.logs = []
  addLog('success', pageText.logCleared)
}

function onCategoryChartRendered() {
  if (state.categoryData.length > 0) {
    addLog('success', pageText.logPieRendered)
  }
}

function onTrendChartRendered() {
  if (state.monthlyTrendData.length > 0) {
    addLog('success', pageText.logLineRendered)
  }
}

onMounted(() => {
  initialize()
})
</script>

<template>
  <div v-loading="loading" class="dashboard-page">
    <el-card shadow="never" class="dashboard-head">
      <div class="head-wrap">
        <div>
          <div class="head-title">{{ pageText.title }}</div>
          <div class="head-subtitle">{{ pageText.subtitle }}</div>
        </div>
        <div class="head-actions">
          <el-button @click="router.push('/ocr')">{{ pageText.goOcr }}</el-button>
          <el-button type="primary" @click="router.push('/receipts')">{{ pageText.goReceiptManage }}</el-button>
        </div>
      </div>
    </el-card>

    <SummaryCards :summary="state.summary" />

    <el-row :gutter="16" class="main-row">
      <el-col :xs="24" :lg="12">
        <CategoryPieChart :data="state.categoryData" @rendered="onCategoryChartRendered" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <MonthlyTrendChart :data="state.monthlyTrendData" @rendered="onTrendChartRendered" />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="main-row">
      <el-col :xs="24" :lg="14">
        <TopExpenseList :list="state.topExpenses" />
      </el-col>
      <el-col :xs="24" :lg="10">
        <LogPanel :logs="state.logs" :loading="loading" @refresh="onRefresh" @clear="onClearLogs" />
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard-page {
  padding: 0 0 18px;
}

.dashboard-head {
  margin-bottom: 16px;
  border: 1px solid #e6e8ef;
}

.head-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.head-actions {
  display: flex;
  gap: 10px;
}

.head-title {
  font-size: 22px;
  font-weight: 700;
  color: #1f2d3d;
}

.head-subtitle {
  margin-top: 4px;
  color: #73809a;
}

.main-row {
  margin-bottom: 16px;
}

@media (max-width: 900px) {
  .head-wrap {
    flex-wrap: wrap;
  }
}
</style>
