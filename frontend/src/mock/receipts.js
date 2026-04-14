const CATEGORY_OPTIONS = [
  '\u9910\u996e',
  '\u4ea4\u901a',
  '\u751f\u6d3b\u7f34\u8d39',
  '\u8d2d\u7269',
  '\u5176\u4ed6'
]

const PAYMENT_METHOD_OPTIONS = [
  '\u652f\u4ed8\u5b9d',
  '\u5fae\u4fe1',
  '\u4f59\u989d',
  '\u94f6\u884c\u5361',
  '\u73b0\u91d1',
  '\u5176\u4ed6'
]

let receipts = [
  {
    id: 1,
    merchant: '\u5357\u4eac\u4f9b\u7535\u516c\u53f8',
    amount: 100.0,
    category: '\u751f\u6d3b\u7f34\u8d39',
    date: '2026-03-06 10:15:28',
    payment_method: '\u4f59\u989d'
  },
  {
    id: 2,
    merchant: '\u8001\u4e61\u9e21',
    amount: 38.5,
    category: '\u9910\u996e',
    date: '2026-03-07 12:05:10',
    payment_method: '\u5fae\u4fe1'
  },
  {
    id: 3,
    merchant: '\u6ef4\u6ef4\u51fa\u884c',
    amount: 26.8,
    category: '\u4ea4\u901a',
    date: '2026-03-08 08:32:45',
    payment_method: '\u652f\u4ed8\u5b9d'
  },
  {
    id: 4,
    merchant: '\u4eac\u4e1c\u8d85\u5e02',
    amount: 236.2,
    category: '\u8d2d\u7269',
    date: '2026-03-10 20:11:03',
    payment_method: '\u94f6\u884c\u5361'
  },
  {
    id: 5,
    merchant: '\u745e\u5e78\u5496\u5561',
    amount: 21.0,
    category: '\u9910\u996e',
    date: '2026-03-11 09:43:22',
    payment_method: '\u652f\u4ed8\u5b9d'
  },
  {
    id: 6,
    merchant: '\u5730\u94c1\u81ea\u52a8\u552e\u7968',
    amount: 6.0,
    category: '\u4ea4\u901a',
    date: '2026-03-12 07:10:09',
    payment_method: '\u5fae\u4fe1'
  },
  {
    id: 7,
    merchant: '\u6c83\u5c14\u739b',
    amount: 319.6,
    category: '\u8d2d\u7269',
    date: '2026-03-14 18:27:59',
    payment_method: '\u94f6\u884c\u5361'
  },
  {
    id: 8,
    merchant: '\u4e2d\u56fd\u79fb\u52a8',
    amount: 89.0,
    category: '\u751f\u6d3b\u7f34\u8d39',
    date: '2026-03-15 14:08:31',
    payment_method: '\u4f59\u989d'
  }
]

function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

function nextId() {
  return receipts.length ? Math.max(...receipts.map((item) => item.id)) + 1 : 1
}

function withLatency(data) {
  return new Promise((resolve) => {
    setTimeout(() => resolve(clone(data)), 120)
  })
}

export async function fetchReceipts() {
  const list = [...receipts].sort((a, b) => (a.date < b.date ? 1 : -1))
  return withLatency({ data: list })
}

export async function createReceipt(payload) {
  const record = {
    id: nextId(),
    merchant: payload.merchant,
    amount: Number(payload.amount),
    category: payload.category,
    date: payload.date,
    payment_method: payload.payment_method
  }

  receipts.unshift(record)
  return withLatency({ data: record })
}

export async function updateReceipt(id, payload) {
  const index = receipts.findIndex((item) => item.id === id)
  if (index === -1) {
    throw new Error('Receipt not found')
  }

  const updated = {
    ...receipts[index],
    merchant: payload.merchant,
    amount: Number(payload.amount),
    category: payload.category,
    date: payload.date,
    payment_method: payload.payment_method
  }

  receipts.splice(index, 1, updated)
  return withLatency({ data: updated })
}

export async function deleteReceipt(id) {
  const index = receipts.findIndex((item) => item.id === id)
  if (index === -1) {
    throw new Error('Receipt not found')
  }

  const deleted = receipts[index]
  receipts.splice(index, 1)
  return withLatency({ data: deleted })
}

export { CATEGORY_OPTIONS, PAYMENT_METHOD_OPTIONS }
