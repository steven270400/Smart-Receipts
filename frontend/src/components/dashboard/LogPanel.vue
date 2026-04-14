<script setup>
defineProps({
  logs: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['refresh', 'clear'])

const labels = {
  title: '\u7cfb\u7edf\u65e5\u5fd7',
  refresh: '\u5237\u65b0\u6570\u636e',
  clear: '\u6e05\u7a7a\u65e5\u5fd7',
  empty: '\u6682\u65e0\u65e5\u5fd7',
  time: '\u65f6\u95f4',
  level: '\u7ea7\u522b',
  message: '\u5185\u5bb9'
}

const levelTagType = {
  info: 'info',
  warning: 'warning',
  error: 'danger',
  success: 'success'
}
</script>

<template>
  <el-card shadow="never" class="log-card">
    <template #header>
      <div class="log-header">
        <div class="card-title">{{ labels.title }}</div>
        <div class="actions">
          <el-button type="primary" :loading="loading" @click="emit('refresh')">{{ labels.refresh }}</el-button>
          <el-button @click="emit('clear')">{{ labels.clear }}</el-button>
        </div>
      </div>
    </template>

    <el-table :data="logs" size="small" height="320" :empty-text="labels.empty">
      <el-table-column prop="time" :label="labels.time" width="170" />
      <el-table-column prop="level" :label="labels.level" width="100">
        <template #default="scope">
          <el-tag :type="levelTagType[scope.row.level] || 'info'" effect="plain">{{ scope.row.level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="message" :label="labels.message" min-width="320" />
    </el-table>
  </el-card>
</template>

<style scoped>
.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 900px) {
  .log-header {
    flex-wrap: wrap;
  }
}
</style>
