<script setup>
import { computed, reactive, ref, watch } from 'vue'

const text = {
  createTitle: '\u65b0\u589e\u8d26\u5355',
  editTitle: '\u7f16\u8f91\u8d26\u5355',
  merchant: '\u5546\u5bb6\u540d\u79f0',
  merchantPlaceholder: '\u8bf7\u8f93\u5165\u5546\u5bb6\u540d\u79f0',
  amount: '\u91d1\u989d',
  amountPlaceholder: '\u8bf7\u8f93\u5165\u91d1\u989d',
  category: '\u5206\u7c7b',
  categoryPlaceholder: '\u8bf7\u9009\u62e9\u5206\u7c7b',
  date: '\u65e5\u671f',
  datePlaceholder: '\u8bf7\u9009\u62e9\u65e5\u671f',
  paymentMethod: '\u652f\u4ed8\u65b9\u5f0f',
  paymentPlaceholder: '\u8bf7\u9009\u62e9\u652f\u4ed8\u65b9\u5f0f',
  cancel: '\u53d6\u6d88',
  confirm: '\u786e\u5b9a',
  requiredMerchant: '\u8bf7\u8f93\u5165\u5546\u5bb6\u540d\u79f0',
  requiredAmount: '\u8bf7\u8f93\u5165\u91d1\u989d',
  invalidAmount: '\u91d1\u989d\u5fc5\u987b\u4e3a\u6709\u6548\u6570\u5b57',
  requiredCategory: '\u8bf7\u9009\u62e9\u5206\u7c7b',
  requiredDate: '\u8bf7\u9009\u62e9\u65e5\u671f',
  requiredPayment: '\u8bf7\u9009\u62e9\u652f\u4ed8\u65b9\u5f0f'
}

const EMPTY_FORM = {
  merchant: '',
  amount: '',
  category: '',
  transaction_time: '',
  payment_method: ''
}

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'create'
  },
  categories: {
    type: Array,
    default: () => []
  },
  paymentMethods: {
    type: Array,
    default: () => []
  },
  initialData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'submit'])

const formRef = ref(null)
const submitting = ref(false)
const form = reactive({ ...EMPTY_FORM })

const title = computed(() => (props.mode === 'edit' ? text.editTitle : text.createTitle))

const rules = {
  merchant: [{ required: true, message: text.requiredMerchant, trigger: 'blur' }],
  amount: [
    { required: true, message: text.requiredAmount, trigger: 'blur' },
    {
      validator: (_, value, callback) => {
        if (value === '' || value === null || value === undefined) {
          callback(new Error(text.requiredAmount))
          return
        }

        if (Number.isNaN(Number(value))) {
          callback(new Error(text.invalidAmount))
          return
        }

        callback()
      },
      trigger: 'blur'
    }
  ],
  category: [{ required: true, message: text.requiredCategory, trigger: 'change' }],
  transaction_time: [{ required: true, message: text.requiredDate, trigger: 'change' }],
  payment_method: [{ required: true, message: text.requiredPayment, trigger: 'change' }]
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) {
      return
    }

    const source = props.mode === 'edit' && props.initialData ? props.initialData : EMPTY_FORM

    form.merchant = source.merchant || ''
    form.amount = source.amount ?? ''
    form.category = source.category || ''
    form.transaction_time = source.transaction_time || ''
    form.payment_method = source.payment_method || ''

    setTimeout(() => {
      formRef.value?.clearValidate()
    }, 0)
  }
)

function closeDialog() {
  emit('update:visible', false)
}

function submit() {
  formRef.value?.validate(async (valid) => {
    if (!valid) {
      return
    }

    submitting.value = true
    try {
      await emit('submit', {
        merchant: form.merchant.trim(),
        amount: Number(form.amount),
        category: form.category,
        transaction_time: form.transaction_time,
        payment_method: form.payment_method
      })
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <el-dialog :model-value="visible" :title="title" width="560px" destroy-on-close @close="closeDialog">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item :label="text.merchant" prop="merchant">
        <el-input v-model="form.merchant" :placeholder="text.merchantPlaceholder" />
      </el-form-item>

      <el-form-item :label="text.amount" prop="amount">
        <el-input v-model="form.amount" :placeholder="text.amountPlaceholder" />
      </el-form-item>

      <el-form-item :label="text.category" prop="category">
        <el-select v-model="form.category" :placeholder="text.categoryPlaceholder" style="width: 100%">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>

      <el-form-item :label="text.date" prop="transaction_time">
        <el-date-picker
          v-model="form.transaction_time"
          type="datetime"
          :placeholder="text.datePlaceholder"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item :label="text.paymentMethod" prop="payment_method">
        <el-select
          v-model="form.payment_method"
          :placeholder="text.paymentPlaceholder"
          style="width: 100%"
        >
          <el-option v-for="item in paymentMethods" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="closeDialog">{{ text.cancel }}</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">{{ text.confirm }}</el-button>
    </template>
  </el-dialog>
</template>
