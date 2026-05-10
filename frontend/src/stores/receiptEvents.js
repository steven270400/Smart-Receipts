import { reactive } from 'vue'

const state = reactive({
  version: 0,
  updatedAt: '',
  reason: ''
})

export function notifyReceiptsChanged(reason = '') {
  state.version += 1
  state.updatedAt = new Date().toISOString()
  state.reason = reason
}

export function useReceiptEventStore() {
  return state
}
