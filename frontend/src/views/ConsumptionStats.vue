<script setup>
import { onMounted, ref, watch } from 'vue'
import PageContainer from '../components/PageContainer.vue'
import SummaryCards from '../components/dashboard/SummaryCards.vue'
import MonthlyTrendChart from '../components/dashboard/MonthlyTrendChart.vue'
import TopExpenseList from '../components/dashboard/TopExpenseList.vue'
import { useAnalyticsData } from '../composables/useAnalyticsData'
import { addOperationLog } from '../stores/operationLog'
import { useReceiptEventStore } from '../stores/receiptEvents'

const loading = ref(false)
const { state, load } = useAnalyticsData()
const receiptEvents = useReceiptEventStore()
const initialized = ref(false)

async function initialize() {
  loading.value = true
  try {
    await load()
    addOperationLog('info', '用户加载消费统计页面数据')
  } catch (error) {
    addOperationLog('error', `消费统计数据加载失败：${error instanceof Error ? error.message : '未知错误'}`)
  } finally {
    loading.value = false
  }
}

watch(
  () => receiptEvents.version,
  async () => {
    if (!initialized.value) {
      return
    }
    await initialize()
  }
)

onMounted(async () => {
  await initialize()
  initialized.value = true
})
</script>

<template>
  <PageContainer title="消费统计" subtitle="查看整体消费规模、趋势与重点消费记录">
    <SummaryCards :summary="state.summary" />

    <el-row :gutter="16">
      <el-col :xs="24" :lg="24">
        <MonthlyTrendChart :data="state.monthlyTrendData" />
      </el-col>
    </el-row>

    <el-card shadow="never" class="sr-card" v-loading="loading">
      <template #header>
        <div class="sr-card-header">最近消费记录</div>
      </template>
      <el-table :data="state.recentExpenses" stripe>
        <el-table-column prop="merchant" label="商家" min-width="180" />
        <el-table-column prop="category" label="分类" min-width="120" />
        <el-table-column prop="paymentMethod" label="支付方式" min-width="120" />
        <el-table-column prop="time" label="时间" min-width="180" />
        <el-table-column label="金额" width="130" align="right">
          <template #default="{ row }">
            CNY {{ Number(row.amount || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无消费记录" />
        </template>
      </el-table>
    </el-card>

    <TopExpenseList :list="state.topExpenses" />
  </PageContainer>
</template>
