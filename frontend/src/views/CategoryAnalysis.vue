<script setup>
import { onMounted, ref, watch } from 'vue'
import PageContainer from '../components/PageContainer.vue'
import CategoryPieChart from '../components/dashboard/CategoryPieChart.vue'
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
    addOperationLog('info', '用户加载分类分析页面数据')
  } catch (error) {
    addOperationLog('error', `分类分析数据加载失败：${error instanceof Error ? error.message : '未知错误'}`)
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
  <PageContainer title="分类分析" subtitle="聚焦分类结构，查看消费集中在哪些分类">
    <CategoryPieChart :data="state.categoryData" />

    <el-row :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="sr-card" v-loading="loading">
          <template #header>
            <div class="sr-card-header">分类消费排行榜</div>
          </template>
          <el-table :data="state.categoryStatsByAmount" stripe>
            <el-table-column prop="category" label="分类" min-width="150" />
            <el-table-column label="消费金额" min-width="120" align="right">
              <template #default="{ row }">
                CNY {{ Number(row.amount || 0).toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="count" label="消费笔数" width="100" align="right" />
            <template #empty>
              <el-empty description="暂无分类数据" />
            </template>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="sr-card" v-loading="loading">
          <template #header>
            <div class="sr-card-header">分类笔数统计</div>
          </template>
          <el-table :data="state.categoryStatsByCount" stripe>
            <el-table-column prop="category" label="分类" min-width="150" />
            <el-table-column prop="count" label="消费笔数" min-width="110" align="right" />
            <el-table-column label="消费金额" min-width="120" align="right">
              <template #default="{ row }">
                CNY {{ Number(row.amount || 0).toFixed(2) }}
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无分类笔数数据" />
            </template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </PageContainer>
</template>
