<script setup>
const props = defineProps({
  list: {
    type: Array,
    required: true
  }
})

const labels = {
  title: '\u8fd16\u4e2a\u6708\u6700\u5927\u6d88\u8d39\u8bb0\u5f55\uff08Top 5\uff09',
  merchant: '\u5546\u5bb6\u540d\u79f0',
  amount: '\u6d88\u8d39\u91d1\u989d',
  category: '\u5206\u7c7b',
  date: '\u65e5\u671f'
}

function toCurrency(amount) {
  return `CNY ${Number(amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
</script>

<template>
  <el-card shadow="never" class="list-card sr-card">
    <template #header>
      <div class="card-title">{{ labels.title }}</div>
    </template>
    <el-table :data="list" stripe>
      <el-table-column prop="merchant" :label="labels.merchant" min-width="180" />
      <el-table-column prop="amount" :label="labels.amount" min-width="140">
        <template #default="scope">
          <span class="amount">{{ toCurrency(scope.row.amount) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="category" :label="labels.category" min-width="120" />
      <el-table-column prop="date" :label="labels.date" min-width="140" />
    </el-table>
  </el-card>
</template>

<style scoped>
.card-title {
  font-size: 15px;
  font-weight: 600;
}

.amount {
  font-weight: 600;
  color: #1f2d3d;
}
</style>
