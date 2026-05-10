import { reactive } from 'vue'

const state = reactive({
  logs: [],
  nextId: 1
})

const MAX_LOGS = 500

function nowText() {
  const now = new Date()
  const pad = (v) => String(v).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

export function addOperationLog(level, message) {
  state.logs.unshift({
    id: state.nextId++,
    time: nowText(),
    level: level || 'info',
    message: message || ''
  })

  if (state.logs.length > MAX_LOGS) {
    state.logs.length = MAX_LOGS
  }
}

export function clearOperationLogs() {
  state.logs.splice(0, state.logs.length)
}

export function useOperationLogStore() {
  return state
}
