<template>
  <div>
    <div class="table-header">
      <div>
        <h2>AI 设置</h2>
        <div class="table-meta">支持 OpenAI / Ollama 切换</div>
      </div>
      <div class="actions">
        <button class="button secondary" @click="testAi" :disabled="testing">
          {{ testing ? '测试中...' : '测试连接' }}
        </button>
      </div>
    </div>

    <div class="config-grid">
      <div class="field">
        <label>AI 供应商</label>
        <select :value="provider" @change="updateField(['provider'], $event.target.value)">
          <option value="openai">OpenAI</option>
          <option value="ollama">Ollama</option>
        </select>
      </div>

      <div class="field">
        <label>最大历史轮次</label>
        <input
          type="number"
          :value="draft.max_history ?? 30"
          @input="updateNumber(['max_history'], $event.target.value)"
        />
      </div>

      <div class="field">
        <label>请求超时（秒）</label>
        <input
          type="number"
          :value="draft.request_timeout_seconds ?? 600"
          @input="updateNumber(['request_timeout_seconds'], $event.target.value)"
        />
      </div>

      <div class="field">
        <label>提示词语料环境变量名</label>
        <input
          type="text"
          :value="draft.prompt_dir_env || ''"
          @input="updateField(['prompt_dir_env'], $event.target.value)"
        />
      </div>

      <div class="field">
        <label>主提示词环境变量名</label>
        <input
          type="text"
          :value="draft.prompt_file_env || ''"
          @input="updateField(['prompt_file_env'], $event.target.value)"
        />
      </div>
    </div>

    <div class="section-block">
      <h3>OpenAI 设置</h3>
      <div class="config-grid">
        <div class="field">
          <label>API 地址</label>
          <input
            type="text"
            :value="draft.openai?.api_base_url || ''"
            @input="updateField(['openai', 'api_base_url'], $event.target.value)"
          />
        </div>
        <div class="field">
          <label>模型名称</label>
          <input
            type="text"
            :value="draft.openai?.model_name || ''"
            @input="updateField(['openai', 'model_name'], $event.target.value)"
          />
        </div>
        <div class="field">
          <label>API Key 环境变量名</label>
          <input
            type="text"
            :value="draft.openai?.api_key_env || ''"
            @input="updateField(['openai', 'api_key_env'], $event.target.value)"
          />
        </div>
      </div>
    </div>

    <div class="section-block">
      <h3>Ollama 设置</h3>
      <div class="config-grid">
        <div class="field">
          <label>API 地址</label>
          <input
            type="text"
            :value="draft.ollama?.base_url || ''"
            @input="updateField(['ollama', 'base_url'], $event.target.value)"
          />
        </div>
        <div class="field">
          <label>模型名称</label>
          <input
            type="text"
            :value="draft.ollama?.model_name || ''"
            @input="updateField(['ollama', 'model_name'], $event.target.value)"
          />
        </div>
        <div class="field toggle-field">
          <label>思考模式</label>
          <input
            type="checkbox"
            :checked="draft.ollama?.thinking_enabled || false"
            @change="updateField(['ollama', 'thinking_enabled'], $event.target.checked)"
          />
        </div>
      </div>
    </div>

    <div v-if="messageOpen" class="modal-backdrop" @click.self="closeMessage">
      <div class="modal">
        <h3>AI 测试结果</h3>
        <pre class="modal-text">{{ messageText }}</pre>
        <div class="actions">
          <button class="button" @click="closeMessage">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { apiPost } from '../api'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const testing = ref(false)
const messageOpen = ref(false)
const messageText = ref('')

const draft = computed(() => props.modelValue || {})
const provider = computed(() => draft.value.provider || 'openai')

function clone(value) {
  if (typeof structuredClone === 'function') {
    return structuredClone(value)
  }
  return JSON.parse(JSON.stringify(value || {}))
}

function updateField(path, value) {
  const next = clone(props.modelValue || {})
  let cursor = next
  for (let i = 0; i < path.length - 1; i += 1) {
    const key = path[i]
    if (!cursor[key] || typeof cursor[key] !== 'object') {
      cursor[key] = {}
    }
    cursor = cursor[key]
  }
  cursor[path[path.length - 1]] = value
  emit('update:modelValue', next)
}

function updateNumber(path, value) {
  const num = Number(value)
  updateField(path, Number.isNaN(num) ? 0 : num)
}

function showMessage(text) {
  messageText.value = text
  messageOpen.value = true
}

function closeMessage() {
  messageOpen.value = false
  messageText.value = ''
}

async function testAi() {
  testing.value = true
  try {
    const data = await apiPost('/api/ai/test', {
      message: 'Hi',
      info2ai: draft.value
    })
    showMessage(data.response || '（无返回内容）')
  } catch (error) {
    showMessage(error.message || '测试失败')
  } finally {
    testing.value = false
  }
}
</script>
