<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">QQ-Guard 控制台</div>
      <nav class="menu">
        <div v-for="group in menuGroups" :key="group.label">
          <div class="section-title">{{ group.label }}</div>
          <button
            v-for="key in group.items"
            :key="key"
            :class="{ active: activeSection === key }"
            @click="activeSection = key"
          >
            {{ sections[key]?.label || key }}
          </button>
        </div>
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
          <button
            class="button"
            @click="saveConfig"
            :disabled="activeSection === chatSectionKey || activeSection === logsSectionKey"
          >
            保存配置
          </button>
        </div>
      </div>

      <ChatView v-if="activeSection === chatSectionKey" />
      <LogView v-else-if="activeSection === logsSectionKey" />
      <section v-else class="panel">
        <h2>{{ sections[activeSection]?.label || '配置面板' }}</h2>
        <div v-if="activeSection && configDraft[activeSection] !== undefined" class="config-grid">
          <AiSettings
            v-if="sections[activeSection]?.type === 'ai'"
            v-model="configDraft[activeSection]"
          />
          <ListTable
            v-else-if="sections[activeSection]?.type === 'list'"
            v-model="configDraft[activeSection]"
            :title="sections[activeSection]?.label"
            :table-key="activeSection"
            :item-type="sections[activeSection]?.itemType || 'string'"
          />
          <ConfigField
            v-else
            v-model="configDraft[activeSection]"
            :label-map="labelMap"
            :path="activeSection"
            :hide-label="true"
          />
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
import ListTable from './components/ListTable.vue'
import AiSettings from './components/AiSettings.vue'
import LogView from './components/LogView.vue'

const configDraft = ref({})
const configVersion = ref(0)
const needsReload = ref(false)
const activeSection = ref('')
const chatSectionKey = '__chat__'
const logsSectionKey = '__logs__'

const sections = {
  app: { label: '基础设置', type: 'config' },
  qq_bot_api: { label: 'NapCat / OneBot 设置', type: 'config' },
  info2ai: { label: 'AI 设置', type: 'ai' },
  monitor_groups: { label: '监控群组', type: 'list', itemType: 'number' },
  admins: { label: '管理员列表', type: 'list', itemType: 'number' },
  white_members: { label: '白名单成员', type: 'list', itemType: 'number' },
  white_groups: { label: '白名单群组', type: 'list', itemType: 'number' },
  website_whitelist: { label: '网站白名单', type: 'list', itemType: 'string' },
  black_rules: { label: '黑名单规则', type: 'list', itemType: 'string' },
  [chatSectionKey]: { label: '聊天记录', type: 'chat' },
  [logsSectionKey]: { label: '日志信息', type: 'logs' }
}

const menuGroups = [
  { label: '系统配置', items: ['app', 'qq_bot_api', 'info2ai'] },
  { label: '监控与规则', items: ['monitor_groups', 'black_rules', 'website_whitelist'] },
  { label: '白名单与管理员', items: ['admins', 'white_members', 'white_groups'] },
  { label: '数据', items: [chatSectionKey, logsSectionKey] }
]
const activeGroupLabel = computed(() => {
  if (!activeSection.value) return ''
  for (const group of menuGroups) {
    if (group.items.includes(activeSection.value)) {
      return group.label
    }
  }
  return ''
})
const activeTitle = computed(() => {
  if (!activeSection.value) return '控制台'
  return activeGroupLabel.value || sections[activeSection.value]?.label || '配置面板'
})

const labelMap = {
  'app.polling_interval': '轮询间隔（秒）',
  'app.chat_history': '聊天记录设置',
  'app.chat_history.max_group_messages': '群聊记录最大保存条数（0 为无限制）',
  'qq_bot_api.mode': '消息接入模式',
  'qq_bot_api.http_url': 'HTTP API 地址',
  'qq_bot_api.ws_url': 'WebSocket 地址',
  'qq_bot_api.token': '鉴权 Token',
  'qq_bot_api.ws_reconnect_seconds': 'WS 重连间隔（秒）',
  'qq_bot_api.ws_ping_interval_seconds': 'WS 心跳间隔（秒）',
  'qq_bot_api.http_post': 'HTTP 上报设置',
  'qq_bot_api.http_post.host': 'HTTP 上报监听地址',
  'qq_bot_api.http_post.port': 'HTTP 上报端口',
  'qq_bot_api.http_post.path': 'HTTP 上报路径',
  'qq_bot_api.http_post.secret': 'HTTP 上报签名密钥',
  'info2ai.provider': 'AI 供应商',
  'info2ai.max_history': '最大历史轮次',
  'info2ai.request_timeout_seconds': '请求超时（秒）',
  'info2ai.prompt_dir_env': '提示词语料环境变量名',
  'info2ai.prompt_file_env': '主提示词环境变量名',
  'info2ai.openai.api_base_url': 'OpenAI API 地址',
  'info2ai.openai.model_name': 'OpenAI 模型',
  'info2ai.openai.api_key_env': 'API Key 环境变量名',
  'info2ai.ollama.base_url': 'Ollama API 地址',
  'info2ai.ollama.model_name': 'Ollama 模型',
  'info2ai.ollama.thinking_enabled': '思考模式'
}

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
  if (!activeSection.value) {
    activeSection.value = 'app'
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
