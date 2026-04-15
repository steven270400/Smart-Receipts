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
      formatter(params) {
        const amount = Number(params.value || 0).toLocaleString('zh-CN', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        })
        return `${params.name}<br/>金额: CNY ${amount}<br/>占比: ${params.percent}%`
      }
    },
    legend: {
      bottom: 0,
      left: 'center'
    },
    series: [
      {
        name: '分类消费',
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
          value: Number(Number(item.amount || 0).toFixed(2))
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
      <div class="card-title">近期消费分类分析（近30天）</div>
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
