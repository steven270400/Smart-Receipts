<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts/dist/echarts.esm.mjs'

const props = defineProps({
  data: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['rendered'])

const chartRef = ref(null)
let chartInstance = null

function buildOption() {
  return {
    color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de'],
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>Amount: CNY {c}<br/>Rate: {d}%'
    },
    legend: {
      bottom: 0,
      left: 'center'
    },
    series: [
      {
        name: 'Category Spend',
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          formatter: '{b}'
        },
        data: props.data.map((item) => ({
          name: item.category,
          value: item.amount
        }))
      }
    ]
  }
}

function renderChart() {
  if (!chartRef.value) {
    return
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  chartInstance.setOption(buildOption())
  emit('rendered')
}

function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

watch(
  () => props.data,
  () => {
    renderChart()
  },
  { deep: true }
)

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<template>
  <el-card shadow="never" class="chart-card">
    <template #header>
      <div class="card-title">近期消费分类分析(Last 30 Days)</div>
    </template>
    <div ref="chartRef" class="chart"></div>
  </el-card>
</template>

<style scoped>
.chart-card {
  height: 100%;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}

.chart {
  width: 100%;
  height: 360px;
}
</style>





