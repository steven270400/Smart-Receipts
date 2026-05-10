<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageContainer from '../components/PageContainer.vue'
import { createCategory, deleteCategory, fetchCategories, renameCategory } from '../api/system'
import { addOperationLog } from '../stores/operationLog'

const loading = ref(false)
const submitting = ref(false)
const rows = ref([])

const createDialogVisible = ref(false)
const createForm = ref({ name: '' })

const editDialogVisible = ref(false)
const editForm = ref({ id: null, name: '' })

function toDateTimeLabel(value) {
  return value || '-'
}

async function loadData() {
  loading.value = true
  try {
    rows.value = await fetchCategories()
    addOperationLog('info', '用户加载分类管理列表数据')
  } catch (error) {
    addOperationLog('error', `分类管理数据加载失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '分类数据加载失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  createForm.value.name = ''
  createDialogVisible.value = true
  addOperationLog('info', '用户打开新增分类弹窗')
}

function openEditDialog(row) {
  editForm.value.id = row.id
  editForm.value.name = row.name
  editDialogVisible.value = true
  addOperationLog('info', `用户打开修改分类弹窗（ID: ${row.id}）`)
}

async function submitCreate() {
  const name = createForm.value.name.trim()
  if (!name) {
    ElMessage.warning('分类名称不能为空')
    return
  }

  submitting.value = true
  try {
    await createCategory({ name })
    createDialogVisible.value = false
    addOperationLog('success', `用户新增分类成功：${name}`)
    ElMessage.success('新增分类成功')
    await loadData()
  } catch (error) {
    addOperationLog('error', `新增分类失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '新增分类失败')
  } finally {
    submitting.value = false
  }
}

async function submitEdit() {
  const id = Number(editForm.value.id)
  const name = editForm.value.name.trim()

  if (!id) {
    ElMessage.error('分类ID无效')
    return
  }
  if (!name) {
    ElMessage.warning('分类名称不能为空')
    return
  }

  submitting.value = true
  try {
    await renameCategory(id, { name })
    editDialogVisible.value = false
    addOperationLog('success', `用户修改分类成功（ID: ${id}）`)
    ElMessage.success('修改分类成功')
    await loadData()
  } catch (error) {
    addOperationLog('error', `修改分类失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '修改分类失败')
  } finally {
    submitting.value = false
  }
}

async function removeCategory(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除分类「${row.name}」吗？若有关联账单将自动迁移到“其他”。`,
      '删除分类',
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
    await deleteCategory(row.id)
    addOperationLog('success', `用户删除分类成功：${row.name}`)
    ElMessage.success('删除分类成功')
    await loadData()
  } catch (error) {
    addOperationLog('error', `删除分类失败：${error instanceof Error ? error.message : '未知错误'}`)
    ElMessage.error(error instanceof Error ? error.message : '删除分类失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <PageContainer title="分类管理" subtitle="维护系统分类（支持新增、修改、删除；默认分类“其他”不可删除/不可修改）">
    <template #actions>
      <el-button type="primary" @click="openCreateDialog">新增分类</el-button>
      <el-button :loading="loading" @click="loadData">刷新</el-button>
    </template>

    <el-card shadow="never" class="sr-card">
      <template #header>
        <div class="sr-card-header">
          <span>分类列表</span>
        </div>
      </template>

      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="name" label="分类" min-width="220" />
        <el-table-column prop="receipt_count" label="关联账单数" width="140" align="right" />
        <el-table-column label="最近使用时间" min-width="200">
          <template #default="{ row }">
            {{ toDateTimeLabel(row.latest_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openEditDialog(row)">修改</el-button>
            <el-button type="danger" link @click="removeCategory(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无分类数据" />
        </template>
      </el-table>
    </el-card>

    <el-dialog v-model="createDialogVisible" title="新增分类" width="460px" destroy-on-close>
      <el-form label-width="92px">
        <el-form-item label="分类名称">
          <el-input v-model="createForm.name" maxlength="100" show-word-limit placeholder="请输入分类名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitCreate">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="修改分类" width="460px" destroy-on-close>
      <el-form label-width="92px">
        <el-form-item label="分类名称">
          <el-input v-model="editForm.name" maxlength="100" show-word-limit placeholder="请输入分类名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitEdit">确定</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

