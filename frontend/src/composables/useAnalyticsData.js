import { reactive } from 'vue'
import { toDateString, toDateTimeString } from '../utils/date'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

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

async function request(url) {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`请求失败，状态码 ${response.status}`)
  }

  const payload = await response.json()
  if (payload.code !== 0) {
    throw new Error(payload.message || '请求失败')
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

function buildCategoryStats(receipts) {
  const categoryMap = {}
  for (const item of receipts) {
    const key = item.category || '其他'
    if (!categoryMap[key]) {
      categoryMap[key] = { category: key, amount: 0, count: 0, latestTime: '' }
    }
    categoryMap[key].amount += Number(item.amount || 0)
    categoryMap[key].count += 1
    const currentTime = String(item.transaction_time || '')
    if (currentTime && (!categoryMap[key].latestTime || currentTime > categoryMap[key].latestTime)) {
      categoryMap[key].latestTime = currentTime
    }
  }

  const list = Object.values(categoryMap).map((item) => ({
    category: item.category,
    amount: round2(item.amount),
    count: item.count,
    latestTime: item.latestTime
  }))

  return {
    listByAmount: [...list].sort((a, b) => b.amount - a.amount),
    listByCount: [...list].sort((a, b) => b.count - a.count)
  }
}

export function useAnalyticsData() {
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
    recentExpenses: [],
    categoryStatsByAmount: [],
    categoryStatsByCount: [],
    overview: {
      totalReceipts: 0,
      todayReceipts: 0,
      categoryCount: 0,
      paymentMethodCount: 0
    }
  })

  async function load() {
    const now = new Date()
    const start30 = new Date(now)
    start30.setDate(start30.getDate() - 30)
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

    const total = last30Rows.reduce((acc, item) => acc + Number(item.amount || 0), 0)
    const categoryStats = buildCategoryStats(last30Rows)
    const topCategory = categoryStats.listByAmount[0] || { category: '', amount: 0 }

    state.summary.last30DaysTotal = round2(total)
    state.summary.last30DaysCount = last30Rows.length
    state.summary.topCategory = topCategory.category
    state.summary.topCategoryAmount = round2(topCategory.amount)

    state.categoryData = categoryStats.listByAmount.map((item) => ({
      category: item.category,
      amount: item.amount
    }))
    state.categoryStatsByAmount = categoryStats.listByAmount
    state.categoryStatsByCount = categoryStats.listByCount

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
    for (const item of rowsWithTime) {
      const t = parseDate(item.transaction_time)
      if (!t) {
        continue
      }
      const key = monthKey(t)
      if (Object.prototype.hasOwnProperty.call(trendMap, key)) {
        trendMap[key] += Number(item.amount || 0)
      }
    }
    state.monthlyTrendData = months.map((month) => ({
      month,
      monthLabel: monthLabel(month),
      amount: round2(trendMap[month])
    }))

    const sorted = [...rowsWithTime].sort((a, b) => Number(b.amount || 0) - Number(a.amount || 0))
    state.topExpenses = sorted.slice(0, 5).map((item) => ({
      id: item.id,
      merchant: item.merchant,
      amount: round2(item.amount),
      category: item.category || '其他',
      date: toDateString(item.transaction_time)
    }))
    state.summary.maxExpenseAmount = round2(state.topExpenses[0]?.amount || 0)

    state.recentExpenses = [...rowsWithTime]
      .sort((a, b) => (a.transaction_time < b.transaction_time ? 1 : -1))
      .slice(0, 10)
      .map((item) => ({
        id: item.id,
        merchant: item.merchant || '-',
        amount: round2(item.amount),
        category: item.category || '其他',
        paymentMethod: item.payment_method || '-',
        time: item.transaction_time || '-'
      }))

    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const todayRows = rowsWithTime.filter((item) => {
      const t = parseDate(item.transaction_time)
      return t && t >= startOfToday
    })
    const categorySet = new Set(rowsWithTime.map((item) => item.category || '其他'))
    const paymentSet = new Set(rowsWithTime.map((item) => item.payment_method || '其他'))

    state.overview.totalReceipts = rowsWithTime.length
    state.overview.todayReceipts = todayRows.length
    state.overview.categoryCount = categorySet.size
    state.overview.paymentMethodCount = paymentSet.size
  }

  return {
    state,
    load
  }
}
