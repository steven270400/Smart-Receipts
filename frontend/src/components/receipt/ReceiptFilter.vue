<script setup>
const DEFAULT_FILTERS = {
  merchant: '',
  category: '',
  payment_method: '',
  dateRange: []
}

const text = {
  merchantLabel: '商家',
  merchantPlaceholder: '请输入商家名称',
  categoryLabel: '分类',
  categoryPlaceholder: '请选择分类',
  paymentLabel: '支付方式',
  paymentPlaceholder: '请选择支付方式',
  dateRangeLabel: '日期范围',
  startDatePlaceholder: '开始日期',
  endDatePlaceholder: '结束日期',
  search: '查询',
  reset: '重置'
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
  <el-card shadow="never" class="sr-card">
    <template #header>
      <div class="sr-card-header">筛选条件</div>
    </template>

    <el-form :model="filters" label-width="98px" class="filter-form">
      <el-row :gutter="12">
        <el-col :xs="24" :md="12" :lg="8">
          <el-form-item :label="text.merchantLabel">
            <el-input
              :model-value="filters.merchant"
              :placeholder="text.merchantPlaceholder"
              clearable
              @update:model-value="(value) => patchFilters({ merchant: value })"
            />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="12" :lg="8">
          <el-form-item :label="text.categoryLabel">
            <el-select
              :model-value="filters.category"
              :placeholder="text.categoryPlaceholder"
              clearable
              style="width: 100%"
              @update:model-value="(value) => patchFilters({ category: value || '' })"
            >
              <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="12" :lg="8">
          <el-form-item :label="text.paymentLabel">
            <el-select
              :model-value="filters.payment_method"
              :placeholder="text.paymentPlaceholder"
              clearable
              style="width: 100%"
              @update:model-value="(value) => patchFilters({ payment_method: value || '' })"
            >
              <el-option v-for="item in paymentMethods" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="16" :lg="12">
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
              style="width: 100%"
              @update:model-value="(value) => patchFilters({ dateRange: value || [] })"
            />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :md="8" :lg="12" class="action-col">
          <el-form-item label-width="0">
            <el-button type="primary" :loading="loading" @click="onSearch">{{ text.search }}</el-button>
            <el-button @click="onReset">{{ text.reset }}</el-button>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </el-card>
</template>

<style scoped>
.filter-form {
  margin-bottom: -6px;
}

.action-col {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 991px) {
  .action-col {
    justify-content: flex-start;
  }
}
</style>
