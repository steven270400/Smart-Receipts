<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const state = reactive({
  loadingUpload: false,
  loadingStats: false,
  loadingReceipts: false,
  errorMessage: '',
  ocrResult: [],
  extractedInfo: null,
  saved: null,
  saveReason: '',
  stats: {
    total_amount: 0,
    total_records: 0,
    category_stats: {}
  },
  receipts: [],
  receiptPage: 1,
  receiptPageSize: 10,
  receiptTotal: 0,
  filters: {
    query: '',
    category: 'all'
  }
})

const router = useRouter()
const selectedFile = ref(null)

const categoryIdMap = ref({})
const categoryIdPrefetching = ref(false)

const categoryOptions = computed(() => {
  const set = new Set()

  for (const name of Object.keys(state.stats?.category_stats || {})) {
    if (name) {
      set.add(String(name))
    }
  }

  for (const row of state.receipts || []) {
    if (row?.category) {
      set.add(String(row.category))
    }
  }
  return ['all', ...Array.from(set)]
})

const filteredReceipts = computed(() => {
  return state.receipts.filter((item) => {
    const categoryOk =
      state.filters.category === 'all' || item.category === state.filters.category

    if (!categoryOk) {
      return false
    }
    return true
  })
})

function saveReasonLabel(reason) {
  const labels = {
    ok: '已保存',
    missing_amount_or_transaction_time: '未保存：缺少金额或交易时间',
    invalid_amount_or_transaction_time: '未保存：金额或交易时间格式不正确'
  }
  return labels[reason] || reason || ''
}

const selectedCategoryId = computed(() => {
  const selected = state.filters.category
  if (!selected || selected === 'all') {
    return null
  }

  const mapped = categoryIdMap.value?.[selected]
  if (mapped) {
    return Number(mapped)
  }

  const row = (state.receipts || []).find((item) => item?.category === selected)
  const id = row?.category_id
  return id ? Number(id) : null
})

const totalPages = computed(() => {
  const total = Number(state.receiptTotal || 0)
  const size = Number(state.receiptPageSize || 10)
  return Math.max(1, Math.ceil(total / size))
})

async function request(url, options = {}) {
  const response = await fetch(url, options)
  let payload = null

  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    throw new Error(payload?.message || `Request failed with status ${response.status}`)
  }

  if (!payload || payload.code !== 0) {
    throw new Error(payload?.message || 'Request failed')
  }

  return payload.data
}

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function uploadReceipt() {
  state.errorMessage = ''

  if (!selectedFile.value) {
    state.errorMessage = '请先选择一张图片。'
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  state.loadingUpload = true
  try {
    const data = await request(`${API_BASE_URL}/ocr`, {
      method: 'POST',
      body: formData
    })

    state.ocrResult = data.ocr_result || []
    state.extractedInfo = data.extracted_info || null
    state.saved = Boolean(data.saved)
    state.saveReason = saveReasonLabel(data.save_reason)

    await Promise.all([loadStats(), loadReceipts(1)])
  } catch (error) {
    state.errorMessage = error instanceof Error ? error.message : '上传失败。'
  } finally {
    state.loadingUpload = false
  }
}

async function loadStats() {
  state.loadingStats = true
  try {
    const payload = await request(`${API_BASE_URL}/statistics`)
    state.stats = payload || {
      total_amount: 0,
      total_records: 0,
      category_stats: {}
    }
  } catch (error) {
    state.errorMessage = error instanceof Error ? error.message : '加载统计概览失败。'
  } finally {
    state.loadingStats = false
  }
}

async function loadReceipts(page = 1) {
  state.loadingReceipts = true
  try {
    const safePage = Math.max(1, Number(page || 1))
    const size = Number(state.receiptPageSize || 10)
    const query = new URLSearchParams({ page: String(safePage), size: String(size) })
    const keyword = state.filters.query.trim()
    if (keyword) {
      query.set('keyword', keyword)
    }
    if (selectedCategoryId.value) {
      query.set('category_id', String(selectedCategoryId.value))
    }
    const payload = await request(`${API_BASE_URL}/receipts?${query.toString()}`)

    state.receipts = payload.list || []
    for (const row of state.receipts) {
      if (row?.category && row?.category_id != null) {
        categoryIdMap.value[String(row.category)] = row.category_id
      }
    }
    state.receiptTotal = payload.pagination?.total ?? 0
    state.receiptPage = payload.pagination?.page ?? safePage
  } catch (error) {
    state.errorMessage = error instanceof Error ? error.message : '加载账单列表失败。'
  } finally {
    state.loadingReceipts = false
  }
}

async function prefetchCategoryIdMap() {
  if (categoryIdPrefetching.value) {
    return
  }
  categoryIdPrefetching.value = true
  try {
    const query = new URLSearchParams({ page: '1', size: '1000' })
    const payload = await request(`${API_BASE_URL}/receipts?${query.toString()}`)
    for (const row of payload.list || []) {
      if (row?.category && row?.category_id != null) {
        categoryIdMap.value[String(row.category)] = row.category_id
      }
    }
  } catch {
    // Best-effort prefetch. If this fails, selection can still fallback to current page mapping.
  } finally {
    categoryIdPrefetching.value = false
  }
}

function goPrevPage() {
  if (state.loadingReceipts || state.receiptPage <= 1) {
    return
  }
  loadReceipts(state.receiptPage - 1)
}

function goNextPage() {
  if (state.loadingReceipts || state.receiptPage >= totalPages.value) {
    return
  }
  loadReceipts(state.receiptPage + 1)
}

watch(
  () => state.filters.category,
  async () => {
    state.receiptPage = 1
    const selected = state.filters.category
    if (selected && selected !== 'all' && categoryIdMap.value?.[selected] == null) {
      await prefetchCategoryIdMap()
    }
    loadReceipts(1)
  }
)

let queryDebounceTimer = null
watch(
  () => state.filters.query,
  () => {
    if (queryDebounceTimer) {
      clearTimeout(queryDebounceTimer)
    }
    queryDebounceTimer = setTimeout(() => {
      state.receiptPage = 1
      loadReceipts(1)
    }, 300)
  }
)

onMounted(async () => {
  await Promise.all([loadStats(), prefetchCategoryIdMap(), loadReceipts(1)])
})
</script>

<template>
  <div class="dashboard">
    <el-breadcrumb separator="/" class="page-breadcrumb">
      <el-breadcrumb-item @click="router.push('/dashboard')">仪表盘</el-breadcrumb-item>
      <el-breadcrumb-item>OCR 控制台</el-breadcrumb-item>
    </el-breadcrumb>

    <header class="hero">
      <p class="eyebrow">SmartReceipts 管理台</p>
      <h1>票据识别与账单管理控制台</h1>
      <div class="hero-row">
        <p class="subtitle">上传票据图片，查看识别与抽取结果，并核对入库数据。</p>
        <div class="hero-actions">
          <el-button @click="router.push('/dashboard')">返回 Dashboard首页</el-button>
          <el-button type="primary" @click="router.push('/receipts')">账单管理</el-button>
        </div>
      </div>
    </header>

    <p v-if="state.errorMessage" class="error">{{ state.errorMessage }}</p>

    <section v-loading="state.loadingUpload" class="panel">
      <div class="panel-head">
        <h2>OCR 上传与解析</h2>
        <button :disabled="state.loadingUpload" @click="uploadReceipt">
          {{ state.loadingUpload ? '上传中...' : '上传并解析' }}
        </button>
      </div>
      <div class="upload-row">
        <input type="file" accept="image/*" @change="onFileChange" />
      </div>
      <p v-if="state.saveReason" class="save-status" :class="{ ok: state.saved, bad: state.saved === false }">
        {{ state.saveReason }}
      </p>

      <div class="results-grid">
        <article>
          <h3>OCR 识别文本</h3>
          <pre>{{ JSON.stringify(state.ocrResult, null, 2) }}</pre>
        </article>
        <article>
          <h3>抽取结果</h3>
          <pre>{{ JSON.stringify(state.extractedInfo, null, 2) }}</pre>
        </article>
      </div>
    </section>

    <section v-loading="state.loadingStats" class="panel">
      <div class="panel-head">
        <h2>统计概览</h2>
        <button :disabled="state.loadingStats" @click="loadStats">
          {{ state.loadingStats ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <span class="label">累计金额</span>
          <strong>{{ Number(state.stats.total_amount || 0).toFixed(2) }}</strong>
        </div>
        <div class="stat-card">
          <span class="label">账单数量</span>
          <strong>{{ state.stats.total_records || 0 }}</strong>
        </div>
      </div>

      <h3>分类汇总</h3>
      <ul class="category-list">
        <li v-for="(amount, category) in state.stats.category_stats" :key="category">
          <span>{{ category }}</span>
          <strong>{{ Number(amount || 0).toFixed(2) }}</strong>
        </li>
      </ul>
    </section>

    <section v-loading="state.loadingReceipts" class="panel">
      <div class="panel-head">
        <h2>账单列表</h2>
        <button :disabled="state.loadingReceipts" @click="loadReceipts(1)">
          {{ state.loadingReceipts ? '刷新中...' : '刷新' }}
        </button>
      </div>

      <div class="filters">
        <input v-model="state.filters.query" type="text" placeholder="搜索商家/日期/分类..." />
        <select v-model="state.filters.category">
          <option v-for="category in categoryOptions" :key="category" :value="category">
            {{ category === 'all' ? '全部分类' : category }}
          </option>
        </select>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>日期</th>
              <th>商家</th>
              <th>分类</th>
              <th>支付方式</th>
              <th class="right">金额</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredReceipts" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.transaction_time || '-' }}</td>
              <td>{{ row.merchant || '-' }}</td>
              <td>{{ row.category || '-' }}</td>
              <td>{{ row.payment_method || '-' }}</td>
              <td class="right">{{ Number(row.amount || 0).toFixed(2) }}</td>
            </tr>
            <tr v-if="!filteredReceipts.length">
              <td colspan="6" class="empty">暂无账单数据</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pager">
        <button :disabled="state.loadingReceipts || state.receiptPage <= 1" @click="goPrevPage">
          上一页
        </button>
        <span class="pager-text">第 {{ state.receiptPage }} / {{ totalPages }} 页（共 {{ state.receiptTotal }} 条）</span>
        <button :disabled="state.loadingReceipts || state.receiptPage >= totalPages" @click="goNextPage">
          下一页
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page-breadcrumb {
  margin-bottom: 12px;
}

.hero-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.pager {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.pager-text {
  color: var(--muted);
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .hero-row {
    flex-wrap: wrap;
  }

  .pager {
    flex-wrap: wrap;
    justify-content: flex-start;
  }
}
</style>
