<template>
  <div class="panel">
    <div class="topbar">
      <h2>日志信息</h2>
      <div class="actions">
        <button class="button secondary" @click="loadLogs">刷新日志</button>
      </div>
    </div>

    <div v-if="updatedAt" class="log-meta">最后更新：{{ updatedAt }}</div>
    <div v-if="errorMessage" class="empty">{{ errorMessage }}</div>
    <div v-else-if="lines.length === 0" class="empty">暂无日志</div>
    <pre v-else class="log-output">{{ content }}</pre>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { apiGet } from '../api'

const lines = ref([])
const updatedAt = ref('')
const errorMessage = ref('')

const content = computed(() => (lines.value || []).join('\n'))

async function loadLogs() {
  errorMessage.value = ''
  try {
    const data = await apiGet('/api/logs/system?limit=200')
    lines.value = data.lines || []
    updatedAt.value = data.updated_at || ''
  } catch (error) {
    errorMessage.value = error.message || '加载日志失败'
  }
}

onMounted(() => {
  loadLogs()
})
</script>
