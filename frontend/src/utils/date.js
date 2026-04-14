export function toDateTimeString(value) {
  if (!value) {
    return ''
  }

  const date = value instanceof Date ? value : new Date(String(value).replace(/-/g, '/'))
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  const pad = (v) => String(v).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function toDateString(value) {
  const datetime = toDateTimeString(value)
  return datetime ? datetime.slice(0, 10) : ''
}

export function toTimestamp(value) {
  const date = new Date(String(value || '').replace(/-/g, '/'))
  if (Number.isNaN(date.getTime())) {
    return 0
  }
  return date.getTime()
}
