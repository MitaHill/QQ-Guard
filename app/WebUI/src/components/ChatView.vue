<template>
  <div class="panel">
    <div class="topbar">
      <h2>聊天记录</h2>
      <div class="actions">
        <button class="button secondary" @click="loadGroups">刷新群组</button>
      </div>
    </div>

    <div v-if="groups.length === 0" class="empty">暂无群聊记录</div>

    <div v-else>
      <div class="chat-tabs">
        <button
          v-for="group in groups"
          :key="group"
          class="chat-tab"
          :class="{ active: activeGroup === group }"
          @click="selectGroup(group)"
        >
          {{ group }}
        </button>
      </div>

      <div class="actions" style="margin-bottom: 16px;">
        <button class="button secondary" @click="refreshMessages" :disabled="!activeGroup">
          刷新记录
        </button>
        <button class="button secondary" @click="loadMore" :disabled="!activeGroup || loadingMore">
          加载更多
        </button>
      </div>

      <div class="export-panel">
        <div class="export-row">
          <span class="export-title">导出当前群聊</span>
          <button class="button secondary" @click="exportGroup('csv')" :disabled="!activeGroup || exporting">
            CSV
          </button>
          <button class="button secondary" @click="exportGroup('yaml')" :disabled="!activeGroup || exporting">
            YAML
          </button>
        </div>
        <div class="export-row">
          <span class="export-title">导出全部群聊（单文件）</span>
          <button class="button secondary" @click="exportAllSingle('csv')" :disabled="exporting">
            CSV
          </button>
          <button class="button secondary" @click="exportAllSingle('yaml')" :disabled="exporting">
            YAML
          </button>
        </div>
        <div class="export-row">
          <span class="export-title">导出全部群聊（分文件压缩包）</span>
          <button class="button secondary" @click="exportAllZip('csv')" :disabled="exporting">
            CSV
          </button>
          <button class="button secondary" @click="exportAllZip('yaml')" :disabled="exporting">
            YAML
          </button>
        </div>
      </div>

      <div v-if="messages.length === 0" class="empty">当前群暂无聊天记录</div>
      <div v-else class="chat-list">
        <div v-for="msg in messages" :key="msg.id" class="chat-card">
          <div class="chat-meta">
            {{ msg.created_at }} · {{ msg.user_id }} · {{ msg.username }}
          </div>
          <div>{{ msg.message || '（空消息）' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { apiDownload, apiGet } from '../api'

const groups = ref([])
const activeGroup = ref('')
const messages = ref([])
const offset = ref(0)
const pageSize = 50
const loadingMore = ref(false)
const exporting = ref(false)
let refreshTimer = null

async function loadGroups() {
  const data = await apiGet('/api/chat/groups')
  groups.value = data.groups || []
  if (!activeGroup.value && groups.value.length > 0) {
    selectGroup(groups.value[0])
  }
}

async function loadMessages(reset = true) {
  if (!activeGroup.value) return
  if (reset) {
    offset.value = 0
    messages.value = []
  }
  const data = await apiGet(`/api/chat/groups/${activeGroup.value}/messages?limit=${pageSize}&offset=${offset.value}`)
  if (reset) {
    messages.value = data.messages || []
  } else {
    messages.value = [...messages.value, ...(data.messages || [])]
  }
}

function selectGroup(group) {
  activeGroup.value = group
  loadMessages(true)
}

function refreshMessages() {
  loadMessages(true)
}

async function loadMore() {
  if (!activeGroup.value) return
  loadingMore.value = true
  offset.value += pageSize
  await loadMessages(false)
  loadingMore.value = false
}

function timestampTag() {
  const now = new Date()
  const pad = value => String(value).padStart(2, '0')
  const y = now.getFullYear()
  const m = pad(now.getMonth() + 1)
  const d = pad(now.getDate())
  const hh = pad(now.getHours())
  const mm = pad(now.getMinutes())
  const ss = pad(now.getSeconds())
  return `${y}${m}${d}_${hh}${mm}${ss}`
}

async function exportGroup(format) {
  if (!activeGroup.value) return
  exporting.value = true
  try {
    const filename = `chat_${activeGroup.value}_${timestampTag()}.${format}`
    await apiDownload(`/api/chat/export/group/${activeGroup.value}?format=${format}`, filename)
  } catch (error) {
    alert(error.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

async function exportAllSingle(format) {
  exporting.value = true
  try {
    const filename = `chat_all_${timestampTag()}.${format}`
    await apiDownload(`/api/chat/export/all?format=${format}`, filename)
  } catch (error) {
    alert(error.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

async function exportAllZip(format) {
  exporting.value = true
  try {
    const filename = `chat_all_${timestampTag()}.zip`
    await apiDownload(`/api/chat/export/all-zip?format=${format}`, filename)
  } catch (error) {
    alert(error.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(() => {
  loadGroups()
  refreshTimer = setInterval(() => {
    if (activeGroup.value) {
      loadMessages(true)
    }
  }, 5000)
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>
