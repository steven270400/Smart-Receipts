<script setup>
defineProps({
  summary: {
    type: Object,
    required: true
  }
})

const labels = {
  total: '近30天消费总额',
  count: '近30天消费笔数',
  topCategory: '近30天最高消费分类',
  maxExpense: '近6个月最大单笔消费',
  countUnit: '笔'
}

function toCurrency(amount) {
  return `CNY ${Number(amount || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
</script>

<template>
  <el-row :gutter="16" class="summary-row">
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="never" class="summary-card sr-card">
        <template #header>{{ labels.total }}</template>
        <div class="value">{{ toCurrency(summary.last30DaysTotal) }}</div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="never" class="summary-card sr-card">
        <template #header>{{ labels.count }}</template>
        <div class="value">{{ summary.last30DaysCount || 0 }} {{ labels.countUnit }}</div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="never" class="summary-card sr-card">
        <template #header>{{ labels.topCategory }}</template>
        <div class="top-category-row">
          <div class="top-category-name">{{ summary.topCategory || '-' }}</div>
          <div class="top-category-amount">{{ toCurrency(summary.topCategoryAmount) }}</div>
        </div>
      </el-card>
    </el-col>
    <el-col :xs="24" :sm="12" :lg="6">
      <el-card shadow="never" class="summary-card sr-card">
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

.value {
  font-size: 24px;
  line-height: 1.3;
  color: var(--el-text-color-primary);
  font-weight: 700;
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
  color: var(--el-text-color-primary);
  font-weight: 700;
}

.top-category-amount {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  white-space: nowrap;
}
</style>