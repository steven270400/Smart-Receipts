<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageContainer from '../components/PageContainer.vue'
import ReceiptFilter from '../components/receipt/ReceiptFilter.vue'
import ReceiptTable from '../components/receipt/ReceiptTable.vue'
import ReceiptFormDialog from '../components/receipt/ReceiptFormDialog.vue'
import { fetchReceipts, createReceipt, updateReceipt, deleteReceipt } from '../api/receipt'
import { fetchCategories, fetchPaymentMethods } from '../api/system'
import { toTimestamp } from '../utils/date'
import { addOperationLog } from '../stores/operationLog'
import { notifyReceiptsChanged } from '../stores/receiptEvents'

const text = {
  pageTitle: '账单管理',
  pageSubtitle: '支持筛选、分页、新增、编辑与删除账单记录',
  addReceipt: '新增账单',
  createSuccess: '账单新增成功',
  updateSuccess: '账单更新成功',
  deleteSuccess: '账单删除成功'
}

const loading = ref(false)
const receipts = ref([])
const categoryOptions = ref([])
const paymentMethodOptions = ref([])

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
    addOperationLog('info', '用户加载账单管理列表数据')
  } catch (error) {
    addOperationLog('error', `加载账单管理列表失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '加载账单失败')
  } finally {
    loading.value = false
  }
}

async function loadDimensions() {
  try {
    const [categories, paymentMethods] = await Promise.all([fetchCategories(), fetchPaymentMethods()])
    categoryOptions.value = (categories || []).map((item) => item.name).filter(Boolean)
    paymentMethodOptions.value = (paymentMethods || []).map((item) => item.name).filter(Boolean)
  } catch (error) {
    addOperationLog('error', `加载分类/支付方式选项失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '加载分类/支付方式选项失败')
  }
}

function handleSearch(model) {
  appliedFilters.value = { ...model }
  pageState.currentPage = 1
  addOperationLog('info', '用户执行账单筛选查询')
}

function handleReset(model) {
  appliedFilters.value = { ...model }
  pageState.currentPage = 1
  addOperationLog('info', '用户重置账单筛选条件')
}

function openCreateDialog() {
  dialogState.mode = 'create'
  dialogState.currentRecord = null
  dialogState.visible = true
  addOperationLog('info', '用户打开新增账单弹窗')
}

function openEditDialog(row) {
  dialogState.mode = 'edit'
  dialogState.currentRecord = { ...row }
  dialogState.visible = true
  addOperationLog('info', `用户打开编辑账单弹窗（ID: ${row?.id || '-'}）`)
}

async function handleDialogSubmit(formData) {
  try {
    if (dialogState.mode === 'create') {
      await createReceipt(formData)
      notifyReceiptsChanged('manual-create')
      addOperationLog('success', '用户新增账单成功')
      ElMessage.success(text.createSuccess)
    } else {
      await updateReceipt(dialogState.currentRecord.id, formData)
      notifyReceiptsChanged('manual-update')
      addOperationLog('success', `用户编辑账单成功（ID: ${dialogState.currentRecord.id}）`)
      ElMessage.success(text.updateSuccess)
    }
    dialogState.visible = false
    await Promise.all([loadData(), loadDimensions()])
  } catch (error) {
    addOperationLog('error', `账单提交失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '提交失败')
  }
}

async function handleDelete(row) {
  try {
    await deleteReceipt(row.id)
    notifyReceiptsChanged('manual-delete')
    addOperationLog('success', `用户删除账单成功（ID: ${row.id}）`)
    ElMessage.success(text.deleteSuccess)

    const nextTotal = filteredList.value.length - 1
    const maxPage = Math.max(1, Math.ceil(Math.max(nextTotal, 0) / pageState.pageSize))
    if (pageState.currentPage > maxPage) {
      pageState.currentPage = maxPage
    }

    await loadData()
  } catch (error) {
    addOperationLog('error', `删除账单失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '删除失败')
  }
}

function handlePageChange(page) {
  pageState.currentPage = page
  addOperationLog('info', `用户切换账单页码至第 ${page} 页`)
}

function handlePageSizeChange(size) {
  pageState.pageSize = size
  pageState.currentPage = 1
  addOperationLog('info', `用户修改账单每页条数为 ${size}`)
}

onMounted(async () => {
  await Promise.all([loadData(), loadDimensions()])
})
</script>

<template>
  <PageContainer :title="text.pageTitle" :subtitle="text.pageSubtitle">
    <template #actions>
      <el-button type="primary" @click="openCreateDialog">{{ text.addReceipt }}</el-button>
    </template>

    <ReceiptFilter
      v-model:filters="filters"
      :categories="categoryOptions"
      :payment-methods="paymentMethodOptions"
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
      :categories="categoryOptions"
      :payment-methods="paymentMethodOptions"
      @submit="handleDialogSubmit"
    />
  </PageContainer>
</template>
