<script setup>
const text = {
  title: '账单列表',
  merchant: '商家',
  amount: '金额',
  category: '分类',
  date: '日期',
  paymentMethod: '支付方式',
  actions: '操作',
  edit: '编辑',
  delete: '删除',
  deleteConfirm: '确定删除这条账单记录吗？'
}

const categoryTagMap = {
  food: 'success',
  transport: 'warning',
  bills: 'primary',
  shopping: 'danger',
  other: 'info'
}

defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  data: {
    type: Array,
    default: () => []
  },
  total: {
    type: Number,
    default: 0
  },
  currentPage: {
    type: Number,
    default: 1
  },
  pageSize: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['edit', 'delete', 'page-change', 'size-change'])

function tagType(category) {
  const key = String(category || '').trim().toLowerCase()
  return categoryTagMap[key] || 'info'
}

function onCurrentChange(page) {
  emit('page-change', page)
}

function onSizeChange(size) {
  emit('size-change', size)
}
</script>

<template>
  <el-card shadow="never" class="sr-card">
    <template #header>
      <div class="sr-card-header">{{ text.title }}</div>
    </template>

    <el-table :data="data" stripe v-loading="loading" row-key="id" empty-text="暂无账单数据">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="merchant" :label="text.merchant" min-width="180" />
      <el-table-column prop="amount" :label="text.amount" width="130" align="right">
        <template #default="{ row }">
          <span class="amount">¥ {{ Number(row.amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="category" :label="text.category" width="120">
        <template #default="{ row }">
          <el-tag :type="tagType(row.category)" effect="plain">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="transaction_time" :label="text.date" min-width="180" />
      <el-table-column prop="payment_method" :label="text.paymentMethod" width="120" />
      <el-table-column :label="text.actions" width="180" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link @click="emit('edit', row)">{{ text.edit }}</el-button>
          <el-popconfirm :title="text.deleteConfirm" @confirm="emit('delete', row)">
            <template #reference>
              <el-button type="danger" link>{{ text.delete }}</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager-wrap">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        :page-sizes="[5, 10, 20]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="onCurrentChange"
        @size-change="onSizeChange"
      />
    </div>
  </el-card>
</template>

<style scoped>
.amount {
  color: var(--el-color-danger);
  font-weight: 700;
}

.pager-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
