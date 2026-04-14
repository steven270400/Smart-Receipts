<script setup>
const DEFAULT_FILTERS = {
  merchant: '',
  category: '',
  payment_method: '',
  dateRange: []
}

const text = {
  merchantLabel: '\u5546\u5bb6\u540d\u79f0',
  merchantPlaceholder: '\u8bf7\u8f93\u5165\u5546\u5bb6\u540d\u79f0',
  categoryLabel: '\u5206\u7c7b',
  categoryPlaceholder: '\u8bf7\u9009\u62e9\u5206\u7c7b',
  paymentLabel: '\u652f\u4ed8\u65b9\u5f0f',
  paymentPlaceholder: '\u8bf7\u9009\u62e9\u652f\u4ed8\u65b9\u5f0f',
  dateRangeLabel: '\u65e5\u671f\u8303\u56f4',
  startDatePlaceholder: '\u5f00\u59cb\u65e5\u671f',
  endDatePlaceholder: '\u7ed3\u675f\u65e5\u671f',
  search: '\u67e5\u8be2',
  reset: '\u91cd\u7f6e'
}

const props = defineProps({
  filters: {
    type: Object,
    required: true
  },
  categories: {
    type: Array,
    default: () => []
  },
  paymentMethods: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:filters', 'search', 'reset'])

function patchFilters(patch) {
  emit('update:filters', {
    ...props.filters,
    ...patch
  })
}

function onSearch() {
  emit('search', { ...props.filters })
}

function onReset() {
  emit('update:filters', { ...DEFAULT_FILTERS })
  emit('reset', { ...DEFAULT_FILTERS })
}
</script>

<template>
  <el-card shadow="never" class="filter-card">
    <el-form :model="filters" inline>
      <el-form-item :label="text.merchantLabel">
        <el-input
          :model-value="filters.merchant"
          :placeholder="text.merchantPlaceholder"
          clearable
          @update:model-value="(value) => patchFilters({ merchant: value })"
        />
      </el-form-item>

      <el-form-item :label="text.categoryLabel">
        <el-select
          :model-value="filters.category"
          :placeholder="text.categoryPlaceholder"
          clearable
          style="width: 140px"
          @update:model-value="(value) => patchFilters({ category: value || '' })"
        >
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>

      <el-form-item :label="text.paymentLabel">
        <el-select
          :model-value="filters.payment_method"
          :placeholder="text.paymentPlaceholder"
          clearable
          style="width: 140px"
          @update:model-value="(value) => patchFilters({ payment_method: value || '' })"
        >
          <el-option v-for="item in paymentMethods" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>

      <el-form-item :label="text.dateRangeLabel">
        <el-date-picker
          :model-value="filters.dateRange"
          type="daterange"
          :start-placeholder="text.startDatePlaceholder"
          :end-placeholder="text.endDatePlaceholder"
          range-separator="至"
          popper-class="receipt-daterange-popper"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @update:model-value="(value) => patchFilters({ dateRange: value || [] })"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="loading" @click="onSearch">{{ text.search }}</el-button>
        <el-button @click="onReset">{{ text.reset }}</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<style scoped>
.filter-card {
  margin-bottom: 16px;
}
</style>
