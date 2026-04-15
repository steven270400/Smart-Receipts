<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ReceiptFilter from '../components/receipt/ReceiptFilter.vue'
import ReceiptTable from '../components/receipt/ReceiptTable.vue'
import ReceiptFormDialog from '../components/receipt/ReceiptFormDialog.vue'
import { fetchReceipts, createReceipt, updateReceipt, deleteReceipt } from '../api/receipt'
import { CATEGORY_OPTIONS, PAYMENT_METHOD_OPTIONS } from '../mock/receipts'
import { toTimestamp } from '../utils/date'

const text = {
  pageTitle: '\u8d26\u5355\u7ba1\u7406',
  pageSubtitle: '\u652f\u6301\u7b5b\u9009\u3001\u5206\u9875\u3001\u65b0\u589e\u3001\u7f16\u8f91\u3001\u5220\u9664\uff08\u6570\u636e\uff09',
  backHome: '\u8fd4\u56de\u9996\u9875',
  addReceipt: '\u65b0\u589e\u8d26\u5355',
  createSuccess: '\u65b0\u589e\u8d26\u5355\u6210\u529f',
  updateSuccess: '\u7f16\u8f91\u8d26\u5355\u6210\u529f',
  deleteSuccess: '\u5220\u9664\u8d26\u5355\u6210\u529f'
}

const router = useRouter()
const loading = ref(false)
const receipts = ref([])

const pageState = reactive({
  currentPage: 1,
  pageSize: 10
})

const filters = ref({
  merchant: '',
  category: '',
  payment_method: '',
  dateRange: []
})

const appliedFilters = ref({ ...filters.value })

const dialogState = reactive({
  visible: false,
  mode: 'create',
  currentRecord: null
})

const filteredList = computed(() => {
  const keyword = appliedFilters.value.merchant.trim().toLowerCase()
  const start = appliedFilters.value.dateRange?.[0]
    ? toTimestamp(`${appliedFilters.value.dateRange[0]} 00:00:00`)
    : 0
  const end = appliedFilters.value.dateRange?.[1]
    ? toTimestamp(`${appliedFilters.value.dateRange[1]} 23:59:59`)
    : 0

  return receipts.value.filter((item) => {
    if (keyword && !String(item.merchant || '').toLowerCase().includes(keyword)) {
      return false
    }

    if (appliedFilters.value.category && item.category !== appliedFilters.value.category) {
      return false
    }

    if (
      appliedFilters.value.payment_method &&
      item.payment_method !== appliedFilters.value.payment_method
    ) {
      return false
    }

    if (start || end) {
      const current = toTimestamp(item.transaction_time)
      if (start && current < start) {
        return false
      }
      if (end && current > end) {
        return false
      }
    }

    return true
  })
})

const pagedList = computed(() => {
  const start = (pageState.currentPage - 1) * pageState.pageSize
  const end = start + pageState.pageSize
  return filteredList.value.slice(start, end)
})

async function loadData() {
  loading.value = true
  try {
    const res = await fetchReceipts({ page: 1, size: 1000 })
    receipts.value = res.list || []
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载账单失败')
  } finally {
    loading.value = false
  }
}

function handleSearch(model) {
  appliedFilters.value = { ...model }
  pageState.currentPage = 1
}

function handleReset(model) {
  appliedFilters.value = { ...model }
  pageState.currentPage = 1
}

function openCreateDialog() {
  dialogState.mode = 'create'
  dialogState.currentRecord = null
  dialogState.visible = true
}

function openEditDialog(row) {
  dialogState.mode = 'edit'
  dialogState.currentRecord = { ...row }
  dialogState.visible = true
}

async function handleDialogSubmit(formData) {
  try {
    if (dialogState.mode === 'create') {
      await createReceipt(formData)
      ElMessage.success(text.createSuccess)
    } else {
      await updateReceipt(dialogState.currentRecord.id, formData)
      ElMessage.success(text.updateSuccess)
    }
    dialogState.visible = false
    await loadData()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '提交失败')
  }
}

async function handleDelete(row) {
  try {
    await deleteReceipt(row.id)
    ElMessage.success(text.deleteSuccess)

    const nextTotal = filteredList.value.length - 1
    const maxPage = Math.max(1, Math.ceil(Math.max(nextTotal, 0) / pageState.pageSize))
    if (pageState.currentPage > maxPage) {
      pageState.currentPage = maxPage
    }

    await loadData()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除失败')
  }
}

function handlePageChange(page) {
  pageState.currentPage = page
}

function handlePageSizeChange(size) {
  pageState.pageSize = size
  pageState.currentPage = 1
}

onMounted(async () => {
  await loadData()
})
</script>

<template>
  <div class="receipt-manage-page">
    <el-card shadow="never" class="page-head">
      <div class="head-wrap">
        <div>
          <div class="head-title">{{ text.pageTitle }}</div>
          <div class="head-subtitle">{{ text.pageSubtitle }}</div>
        </div>
        <div class="head-actions">
          <el-button @click="router.push('/dashboard')">{{ text.backHome }}</el-button>
          <el-button @click="router.push('/ocr')">前往 OCR 控制台</el-button>
          <el-button type="primary" @click="openCreateDialog">{{ text.addReceipt }}</el-button>
        </div>
      </div>
    </el-card>

    <ReceiptFilter
      v-model:filters="filters"
      :categories="CATEGORY_OPTIONS"
      :payment-methods="PAYMENT_METHOD_OPTIONS"
      :loading="loading"
      @search="handleSearch"
      @reset="handleReset"
    />

    <ReceiptTable
      :loading="loading"
      :data="pagedList"
      :total="filteredList.length"
      :current-page="pageState.currentPage"
      :page-size="pageState.pageSize"
      @edit="openEditDialog"
      @delete="handleDelete"
      @page-change="handlePageChange"
      @size-change="handlePageSizeChange"
    />

    <ReceiptFormDialog
      v-model:visible="dialogState.visible"
      :mode="dialogState.mode"
      :initial-data="dialogState.currentRecord"
      :categories="CATEGORY_OPTIONS"
      :payment-methods="PAYMENT_METHOD_OPTIONS"
      @submit="handleDialogSubmit"
    />
  </div>
</template>

<style scoped>
.receipt-manage-page {
  padding: 0 0 18px;
}

.page-head {
  margin-bottom: 16px;
  border: 1px solid #e6e8ef;
}

.head-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
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

.head-actions {
  display: flex;
  gap: 10px;
}

@media (max-width: 900px) {
  .head-wrap {
    flex-wrap: wrap;
  }
}
</style>
