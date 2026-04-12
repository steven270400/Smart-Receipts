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
    color: ['#2f7ed8'],
    tooltip: {
      trigger: 'axis',
      formatter(params) {
        const item = params[0]
        return `${item.axisValue}<br/>Amount: CNY ${item.data}`
      }
    },
    grid: {
      left: 24,
      right: 24,
      top: 24,
      bottom: 24,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.data.map((item) => item.month)
    },
    yAxis: {
      type: 'value',
      name: 'Amount'
    },
    series: [
      {
        name: 'Monthly Spend',
        type: 'line',
        smooth: true,
        symbolSize: 8,
        data: props.data.map((item) => item.amount),
        areaStyle: {
          opacity: 0.15
        }
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
      <div class="card-title">3-Month Trend</div>
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





