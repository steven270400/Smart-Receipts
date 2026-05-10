<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import PageContainer from '../components/PageContainer.vue'
import { addOperationLog } from '../stores/operationLog'
import { notifyReceiptsChanged } from '../stores/receiptEvents'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const state = reactive({
  loadingUpload: false,
  loadingStats: false,
  loadingReceipts: false,
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

async function request(url, options = {}) {
  const response = await fetch(url, options)
  let payload = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    throw new Error(payload?.message || `请求失败，状态码 ${response.status}`)
  }
  if (!payload || payload.code !== 0) {
    throw new Error(payload?.message || '请求失败')
  }
  return payload.data
}

function saveReasonLabel(reason) {
  const labels = {
    ok: '已保存',
    missing_amount_or_transaction_time: '未保存：缺少金额或交易时间',
    invalid_amount_or_transaction_time: '未保存：金额或交易时间格式不正确'
  }
  return labels[reason] || reason || ''
}

function onUploadFileChange(uploadFile) {
  selectedFile.value = uploadFile?.raw || null
}

async function uploadReceipt() {
  if (!selectedFile.value) {
    addOperationLog('warning', 'OCR 上传失败：用户未选择图片')
    ElMessage.warning('请先选择图片')
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
    if (state.saved) {
      notifyReceiptsChanged('ocr')
    }
    await Promise.all([loadStats(), loadReceipts(1)])
    addOperationLog('success', '用户完成 OCR 识别并刷新统计与账单列表')
    ElMessage.success('OCR 识别完成')
  } catch (error) {
    addOperationLog('error', `OCR 上传识别失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '上传失败')
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
    addOperationLog('info', '用户刷新 OCR 统计概览')
  } catch (error) {
    addOperationLog('error', `加载 OCR 统计失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '加载统计失败')
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
    addOperationLog('info', `用户查看 OCR 页账单列表（第 ${state.receiptPage} 页）`)
  } catch (error) {
    addOperationLog('error', `加载 OCR 页账单失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '加载账单失败')
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
    // best effort
  } finally {
    categoryIdPrefetching.value = false
  }
}

function onPageChange(page) {
  loadReceipts(page)
}

watch(
  () => state.filters.category,
  async () => {
    if (
      state.filters.category &&
      state.filters.category !== 'all' &&
      categoryIdMap.value?.[state.filters.category] == null
    ) {
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
      loadReceipts(1)
    }, 300)
  }
)

onMounted(async () => {
  await Promise.all([loadStats(), prefetchCategoryIdMap(), loadReceipts(1)])
})
</script>

<template>
  <PageContainer
    title="OCR 控制台"
    subtitle="上传票据图片、查看识别结果并核对入库记录"
  >
    <template #actions>
      <el-button @click="loadStats" :loading="state.loadingStats">刷新统计</el-button>
      <el-button type="primary" @click="uploadReceipt" :loading="state.loadingUpload">
        上传并识别
      </el-button>
    </template>

    <el-card shadow="never" class="sr-card">
      <template #header>
        <div class="sr-card-header">OCR 上传与解析</div>
      </template>
      <el-upload
        class="upload-block"
        :auto-upload="false"
        :limit="1"
        :on-change="onUploadFileChange"
        :show-file-list="true"
      >
        <template #trigger>
          <el-button>选择图片</el-button>
        </template>
      </el-upload>
      <p v-if="state.saveReason" class="save-status" :class="{ ok: state.saved, bad: state.saved === false }">
        {{ state.saveReason }}
      </p>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="12">
          <el-card shadow="never" class="inner-card">
            <template #header>
              <div class="sr-card-header">OCR 原始文本</div>
            </template>
            <pre>{{ JSON.stringify(state.ocrResult, null, 2) }}</pre>
          </el-card>
        </el-col>
        <el-col :xs="24" :lg="12">
          <el-card shadow="never" class="inner-card">
            <template #header>
              <div class="sr-card-header">抽取字段</div>
            </template>
            <pre>{{ JSON.stringify(state.extractedInfo, null, 2) }}</pre>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="sr-card" v-loading="state.loadingStats">
      <template #header>
        <div class="sr-card-header">统计概览</div>
      </template>
      <div class="stats-grid">
        <div class="metric">
          <span>总金额</span>
          <strong>{{ Number(state.stats.total_amount || 0).toFixed(2) }}</strong>
        </div>
        <div class="metric">
          <span>总记录数</span>
          <strong>{{ state.stats.total_records || 0 }}</strong>
        </div>
      </div>

      <el-table
        :data="Object.entries(state.stats.category_stats || {}).map(([category, amount]) => ({ category, amount }))"
        stripe
      >
        <el-table-column prop="category" label="分类" min-width="180" />
        <el-table-column label="金额" min-width="140" align="right">
          <template #default="{ row }">
            {{ Number(row.amount || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无分类汇总数据" />
        </template>
      </el-table>
    </el-card>

    <el-card shadow="never" class="sr-card" v-loading="state.loadingReceipts">
      <template #header>
        <div class="sr-card-header">账单列表</div>
      </template>

      <div class="filters">
        <el-input v-model="state.filters.query" clearable placeholder="搜索商家/日期/分类..." />
        <el-select v-model="state.filters.category">
          <el-option v-for="item in categoryOptions" :key="item" :value="item" :label="item === 'all' ? '全部分类' : item" />
        </el-select>
      </div>

      <el-table :data="state.receipts" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="transaction_time" label="日期" min-width="180" />
        <el-table-column prop="merchant" label="商家" min-width="160" />
        <el-table-column prop="category" label="分类" min-width="120" />
        <el-table-column prop="payment_method" label="支付方式" min-width="120" />
        <el-table-column label="金额" min-width="120" align="right">
          <template #default="{ row }">
            {{ Number(row.amount || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无账单数据" />
        </template>
      </el-table>

      <div class="pager-wrap">
        <el-pagination
          :current-page="state.receiptPage"
          :page-size="state.receiptPageSize"
          :total="state.receiptTotal"
          layout="total, prev, pager, next"
          @current-change="onPageChange"
        />
      </div>
    </el-card>
  </PageContainer>
</template>

<style scoped>
.upload-block {
  margin-bottom: 12px;
}

.save-status {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
}

.save-status.ok {
  color: var(--el-color-success);
}

.save-status.bad {
  color: var(--el-color-danger);
}

.inner-card {
  margin-top: 8px;
}

.inner-card :deep(.el-card__body) {
  padding-top: 0;
}

pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.metric {
  border: 1px solid var(--el-border-color-light);
  border-radius: 10px;
  padding: 12px;
  background: var(--el-fill-color-extra-light);
}

.metric span {
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.metric strong {
  display: block;
  margin-top: 6px;
  font-size: 24px;
  line-height: 1.2;
}

.filters {
  margin-bottom: 14px;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
}

.pager-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .stats-grid,
  .filters {
    grid-template-columns: 1fr;
  }
}
</style>
