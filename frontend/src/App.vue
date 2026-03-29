<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const state = reactive({
  loadingUpload: false,
  loadingStats: false,
  loadingReceipts: false,
  errorMessage: '',
  ocrResult: [],
  extractedInfo: null,
  saved: null,
  saveReason: '',
  stats: {
    total_amount: 0,
    total_records: 0,
    category_stats: {}
  },
  receipts: [],
  filters: {
    query: '',
    category: 'all'
  }
})

const selectedFile = ref(null)

const categories = computed(() => {
  const set = new Set()
  for (const row of state.receipts) {
    if (row.category) {
      set.add(row.category)
    }
  }
  return ['all', ...Array.from(set)]
})

const filteredReceipts = computed(() => {
  const query = state.filters.query.trim().toLowerCase()
  return state.receipts.filter((item) => {
    const categoryOk =
      state.filters.category === 'all' || item.category === state.filters.category

    if (!categoryOk) {
      return false
    }

    if (!query) {
      return true
    }

    return [item.merchant, item.category, item.payment_method, item.date]
      .filter(Boolean)
      .some((value) => String(value).toLowerCase().includes(query))
  })
})

function saveReasonLabel(reason) {
  const labels = {
    ok: 'Saved',
    missing_amount_or_date: 'Not saved: missing amount or date',
    invalid_amount_or_date: 'Not saved: invalid amount or date'
  }
  return labels[reason] || reason || ''
}

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function uploadReceipt() {
  state.errorMessage = ''

  if (!selectedFile.value) {
    state.errorMessage = 'Please choose an image first.'
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  state.loadingUpload = true
  try {
    const response = await fetch(`${API_BASE_URL}/ocr`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`)
    }

    const data = await response.json()
    state.ocrResult = data.ocr_result || []
    state.extractedInfo = data.extracted_info || null
    state.saved = Boolean(data.saved)
    state.saveReason = saveReasonLabel(data.save_reason)

    await Promise.all([loadStats(), loadReceipts()])
  } catch (error) {
    state.errorMessage = error instanceof Error ? error.message : 'Upload failed.'
  } finally {
    state.loadingUpload = false
  }
}

async function loadStats() {
  state.loadingStats = true
  try {
    const response = await fetch(`${API_BASE_URL}/statistics`)
    if (!response.ok) {
      throw new Error(`Stats request failed with status ${response.status}`)
    }

    const payload = await response.json()
    state.stats = payload.data || {
      total_amount: 0,
      total_records: 0,
      category_stats: {}
    }
  } catch (error) {
    state.errorMessage = error instanceof Error ? error.message : 'Failed to load statistics.'
  } finally {
    state.loadingStats = false
  }
}

async function loadReceipts() {
  state.loadingReceipts = true
  try {
    const response = await fetch(`${API_BASE_URL}/receipts`)
    if (!response.ok) {
      throw new Error(`Receipts request failed with status ${response.status}`)
    }

    const payload = await response.json()
    state.receipts = payload.data || []
  } catch (error) {
    state.errorMessage = error instanceof Error ? error.message : 'Failed to load receipts.'
  } finally {
    state.loadingReceipts = false
  }
}

onMounted(async () => {
  await Promise.all([loadStats(), loadReceipts()])
})
</script>

<template>
  <div class="dashboard">
    <header class="hero">
      <p class="eyebrow">SmartReceipts Admin</p>
      <h1>Database Management Console</h1>
      <p class="subtitle">
        Upload receipts, monitor extraction quality, and inspect stored records.
      </p>
    </header>

    <p v-if="state.errorMessage" class="error">{{ state.errorMessage }}</p>

    <section class="panel">
      <div class="panel-head">
        <h2>OCR Intake</h2>
        <button :disabled="state.loadingUpload" @click="uploadReceipt">
          {{ state.loadingUpload ? 'Uploading...' : 'Upload And Parse' }}
        </button>
      </div>
      <div class="upload-row">
        <input type="file" accept="image/*" @change="onFileChange" />
      </div>
      <p v-if="state.saveReason" class="save-status" :class="{ ok: state.saved, bad: state.saved === false }">
        {{ state.saveReason }}
      </p>

      <div class="results-grid">
        <article>
          <h3>OCR Text</h3>
          <pre>{{ JSON.stringify(state.ocrResult, null, 2) }}</pre>
        </article>
        <article>
          <h3>Extracted Receipt Info</h3>
          <pre>{{ JSON.stringify(state.extractedInfo, null, 2) }}</pre>
        </article>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2>Statistics</h2>
        <button :disabled="state.loadingStats" @click="loadStats">
          {{ state.loadingStats ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <span class="label">Total Amount</span>
          <strong>{{ Number(state.stats.total_amount || 0).toFixed(2) }}</strong>
        </div>
        <div class="stat-card">
          <span class="label">Receipt Count</span>
          <strong>{{ state.stats.total_records || 0 }}</strong>
        </div>
      </div>

      <h3>Category Breakdown</h3>
      <ul class="category-list">
        <li v-for="(amount, category) in state.stats.category_stats" :key="category">
          <span>{{ category }}</span>
          <strong>{{ Number(amount || 0).toFixed(2) }}</strong>
        </li>
      </ul>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2>Receipts</h2>
        <button :disabled="state.loadingReceipts" @click="loadReceipts">
          {{ state.loadingReceipts ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>

      <div class="filters">
        <input v-model="state.filters.query" type="text" placeholder="Search merchant, date, category..." />
        <select v-model="state.filters.category">
          <option v-for="category in categories" :key="category" :value="category">
            {{ category === 'all' ? 'All Categories' : category }}
          </option>
        </select>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Date</th>
              <th>Merchant</th>
              <th>Category</th>
              <th>Method</th>
              <th class="right">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in filteredReceipts" :key="row.id">
              <td>{{ row.id }}</td>
              <td>{{ row.date || '-' }}</td>
              <td>{{ row.merchant || '-' }}</td>
              <td>{{ row.category || '-' }}</td>
              <td>{{ row.payment_method || '-' }}</td>
              <td class="right">{{ Number(row.amount || 0).toFixed(2) }}</td>
            </tr>
            <tr v-if="!filteredReceipts.length">
              <td colspan="6" class="empty">No receipts to show.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
