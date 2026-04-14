<script setup>
const props = defineProps({
  summary: {
    type: Object,
    required: true
  }
})

const labels = {
  total: '\u8fd130\u5929\u6d88\u8d39\u603b\u989d',
  count: '\u8fd130\u5929\u6d88\u8d39\u7b14\u6570',
  topCategory: '\u8fd130\u5929\u6d88\u8d39\u6700\u9ad8\u5206\u7c7b',
  maxExpense: '\u8fd16\u4e2a\u6708\u6700\u5927\u5355\u7b14\u6d88\u8d39\u91d1\u989d',
  countUnit: '\u7b14'
}

function toCurrency(amount) {
  return `CNY ${Number(amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
</script>

<template>
  <el-row :gutter="16" class="summary-row">
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="hover" class="summary-card">
        <template #header>{{ labels.total }}</template>
        <div class="value">{{ toCurrency(summary.last30DaysTotal) }}</div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="hover" class="summary-card">
        <template #header>{{ labels.count }}</template>
        <div class="value">{{ summary.last30DaysCount || 0 }} {{ labels.countUnit }}</div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="hover" class="summary-card">
        <template #header>{{ labels.topCategory }}</template>
        <div class="top-category-row">
          <div class="top-category-name">{{ summary.topCategory || '-' }}</div>
          <div class="top-category-amount">{{ toCurrency(summary.topCategoryAmount) }}</div>
        </div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="hover" class="summary-card">
        <template #header>{{ labels.maxExpense }}</template>
        <div class="value">{{ toCurrency(summary.maxExpenseAmount) }}</div>
      </el-card>
    </el-col>
  </el-row>
</template>

<style scoped>
.summary-row {
  margin-bottom: 16px;
}

.summary-card :deep(.el-card__header) {
  font-size: 14px;
  color: #5f697c;
  padding: 14px 16px;
}

.summary-card :deep(.el-card__body) {
  padding: 12px 16px 16px;
}

.value {
  font-size: 24px;
  line-height: 1.3;
  color: #1f2d3d;
  font-weight: 700;
}

.sub {
  margin-top: 6px;
  color: #77829a;
  font-size: 13px;
}

.top-category-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}

.top-category-name {
  font-size: 20px;
  line-height: 1.3;
  color: #1f2d3d;
  font-weight: 700;
}

.top-category-amount {
  color: #77829a;
  font-size: 13px;
  white-space: nowrap;
}
</style>
