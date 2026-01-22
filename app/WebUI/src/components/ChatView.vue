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
import { onMounted, ref } from 'vue'
import { apiGet } from '../api'

const groups = ref([])
const activeGroup = ref('')
const messages = ref([])
const offset = ref(0)
const pageSize = 50
const loadingMore = ref(false)

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

onMounted(() => {
  loadGroups()
})
</script>
