<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageContainer from '../components/PageContainer.vue'
import {
  createPaymentMethod,
  deletePaymentMethod,
  fetchPaymentMethods,
  renamePaymentMethod
} from '../api/system'
import { addOperationLog } from '../stores/operationLog'

const loading = ref(false)
const submitting = ref(false)
const rows = ref([])

const createDialogVisible = ref(false)
const editDialogVisible = ref(false)

const createForm = ref({ name: '' })
const editForm = ref({ id: null, name: '' })

function toDateTimeLabel(value) {
  return value || '-'
}

async function loadData() {
  loading.value = true
  try {
    rows.value = await fetchPaymentMethods()
    addOperationLog('info', '用户加载支付方式管理列表数据')
  } catch (error) {
    addOperationLog('error', `支付方式管理数据加载失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '支付方式数据加载失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  createForm.value.name = ''
  createDialogVisible.value = true
  addOperationLog('info', '用户打开新增支付方式弹窗')
}

function openEditDialog(row) {
  editForm.value.id = row.id
  editForm.value.name = row.name
  editDialogVisible.value = true
  addOperationLog('info', `用户打开编辑支付方式弹窗（ID: ${row.id}）`)
}

async function submitCreate() {
  const name = createForm.value.name.trim()
  if (!name) {
    ElMessage.warning('支付方式名称不能为空')
    return
  }

  submitting.value = true
  try {
    await createPaymentMethod({ name })
    createDialogVisible.value = false
    addOperationLog('success', `用户新增支付方式成功：${name}`)
    ElMessage.success('新增支付方式成功')
    await loadData()
  } catch (error) {
    addOperationLog('error', `新增支付方式失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '新增支付方式失败')
  } finally {
    submitting.value = false
  }
}

async function submitEdit() {
  const id = Number(editForm.value.id)
  const name = editForm.value.name.trim()
  if (!id) {
    ElMessage.error('支付方式ID无效')
    return
  }
  if (!name) {
    ElMessage.warning('支付方式名称不能为空')
    return
  }

  submitting.value = true
  try {
    await renamePaymentMethod(id, { name })
    editDialogVisible.value = false
    addOperationLog('success', `用户修改支付方式成功（ID: ${id}）`)
    ElMessage.success('修改支付方式成功')
    await loadData()
  } catch (error) {
    addOperationLog('error', `修改支付方式失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '修改支付方式失败')
  } finally {
    submitting.value = false
  }
}

async function removePaymentMethod(row) {
  if (row?.name === '其他') {
    ElMessage.warning('默认支付方式不允许删除')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定删除支付方式「${row.name}」吗？若有关联账单将自动迁移到“其他”。`,
      '删除支付方式',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  loading.value = true
  try {
    await deletePaymentMethod(row.id)
    addOperationLog('success', `用户删除支付方式成功：${row.name}`)
    ElMessage.success('删除支付方式成功')
    await loadData()
  } catch (error) {
    addOperationLog('error', `删除支付方式失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '删除支付方式失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <PageContainer title="支付方式管理" subtitle="维护系统支付方式（支持新增、修改、删除；默认“其他”不可删除）">
    <template #actions>
      <el-button type="primary" @click="openCreateDialog">新增支付方式</el-button>
      <el-button :loading="loading" @click="loadData">刷新</el-button>
    </template>

    <el-card shadow="never" class="sr-card">
      <template #header>
        <div class="sr-card-header">
          <span>支付方式列表</span>
        </div>
      </template>
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="name" label="支付方式" min-width="220" />
        <el-table-column prop="receipt_count" label="关联账单数" width="140" align="right" />
        <el-table-column label="最近使用时间" min-width="200">
          <template #default="{ row }">
            {{ toDateTimeLabel(row.latest_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">修改</el-button>
            <el-button v-if="row.name !== '其他'" type="danger" link @click="removePaymentMethod(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无支付方式数据" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="createDialogVisible" title="新增支付方式" width="460px" destroy-on-close>
      <el-form label-width="106px">
        <el-form-item label="支付方式名称">
          <el-input v-model="createForm.name" maxlength="100" show-word-limit placeholder="请输入支付方式名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="修改支付方式" width="460px" destroy-on-close>
      <el-form label-width="106px">
        <el-form-item label="支付方式名称">
          <el-input v-model="editForm.name" maxlength="100" show-word-limit placeholder="请输入支付方式名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitEdit">确定</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

