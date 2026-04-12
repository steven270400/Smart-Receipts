<script setup>
const text = {
  merchant: '\u5546\u5bb6',
  amount: '\u91d1\u989d',
  category: '\u5206\u7c7b',
  date: '\u65e5\u671f',
  paymentMethod: '\u652f\u4ed8\u65b9\u5f0f',
  actions: '\u64cd\u4f5c',
  edit: '\u7f16\u8f91',
  delete: '\u5220\u9664',
  deleteConfirm: '\u786e\u8ba4\u5220\u9664\u8be5\u8d26\u5355\u5417\uff1f'
}

const categoryTagMap = {
  '\u9910\u996e': 'success',
  '\u4ea4\u901a': 'warning',
  '\u751f\u6d3b\u7f34\u8d39': 'primary',
  '\u8d2d\u7269': 'danger',
  '\u5176\u4ed6': 'info'
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
  return categoryTagMap[category] || 'info'
}

function onCurrentChange(page) {
  emit('page-change', page)
}

function onSizeChange(size) {
  emit('size-change', size)
}
</script>

<template>
  <el-card shadow="never">
    <el-table :data="data" border stripe v-loading="loading" row-key="id">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="merchant" :label="text.merchant" min-width="180" />
      <el-table-column prop="amount" :label="text.amount" width="130" align="right">
        <template #default="{ row }">
          <span class="amount">¥ {{ Number(row.amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="category" :label="text.category" width="120">
        <template #default="{ row }">
          <el-tag :type="tagType(row.category)">{{ row.category }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="date" :label="text.date" min-width="180" />
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
  color: #d45050;
  font-weight: 700;
}

.pager-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>