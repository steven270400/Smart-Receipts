<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <section class="page-container">
    <header class="page-header">
      <div>
        <h1 class="page-title">{{ title }}</h1>
        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="page-actions">
        <slot name="actions" />
      </div>
    </header>

    <div class="page-content">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.page-container {
  display: grid;
  gap: 16px;
}

.page-header {
  background: #ffffff;
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  min-height: 78px;
  padding: 14px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  line-height: 1.35;
  color: var(--el-text-color-primary);
}

.page-subtitle {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.page-content {
  display: grid;
  gap: 16px;
}

@media (max-width: 900px) {
  .page-header {
    flex-wrap: wrap;
  }

  .page-title {
    font-size: 20px;
  }
}
</style>
