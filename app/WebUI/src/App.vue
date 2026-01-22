<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">QQ-Guard 控制台</div>
      <nav class="menu">
        <div class="section-title">配置面板</div>
        <button
          v-for="key in configKeys"
          :key="key"
          :class="{ active: activeSection === key }"
          @click="activeSection = key"
        >
          {{ key }}
        </button>
        <div class="section-title">数据</div>
        <button
          :class="{ active: activeSection === chatSectionKey }"
          @click="activeSection = chatSectionKey"
        >
          聊天记录
        </button>
      </nav>
    </aside>

    <main class="content">
      <div class="topbar">
        <h1>{{ activeTitle }}</h1>
        <div class="actions">
          <div class="indicator" :class="{ alert: needsReload }">
            <span class="dot"></span>
            <span>{{ needsReload ? '检测到配置更新' : '热重载已同步' }}</span>
          </div>
          <button class="button secondary" @click="reloadConfig">同步</button>
          <button class="button" @click="saveConfig" :disabled="activeSection === chatSectionKey">
            保存配置
          </button>
        </div>
      </div>

      <ChatView v-if="activeSection === chatSectionKey" />
      <section v-else class="panel">
        <h2>配置项：{{ activeSection }}</h2>
        <div v-if="activeSection && configDraft[activeSection] !== undefined" class="config-grid">
          <ConfigField v-model="configDraft[activeSection]" />
        </div>
        <div v-else class="empty">请选择需要编辑的配置模块</div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { apiGet, apiPut } from './api'
import ConfigField from './components/ConfigField.vue'
import ChatView from './components/ChatView.vue'

const configDraft = ref({})
const configVersion = ref(0)
const needsReload = ref(false)
const activeSection = ref('')
const chatSectionKey = '__chat__'

const configKeys = computed(() => Object.keys(configDraft.value || {}))
const activeTitle = computed(() => {
  if (activeSection.value === chatSectionKey) return '群聊记录'
  return activeSection.value ? `配置 - ${activeSection.value}` : '配置面板'
})

function cloneConfig(data) {
  if (typeof structuredClone === 'function') {
    return structuredClone(data)
  }
  return JSON.parse(JSON.stringify(data))
}

async function reloadConfig() {
  const data = await apiGet('/api/config')
  configDraft.value = cloneConfig(data.config || {})
  configVersion.value = data.version || 0
  needsReload.value = false
  if (!activeSection.value && configKeys.value.length > 0) {
    activeSection.value = configKeys.value[0]
  }
}

async function saveConfig() {
  await apiPut('/api/config', configDraft.value)
  await reloadConfig()
}

async function checkConfigVersion() {
  const data = await apiGet('/api/config/version')
  const version = data.version || 0
  if (version !== configVersion.value) {
    needsReload.value = true
  }
}

onMounted(async () => {
  await reloadConfig()
  setInterval(checkConfigVersion, 2000)
})
</script>
