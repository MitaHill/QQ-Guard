<template>
  <div class="table-panel">
    <div class="table-header">
      <div>
        <h2>{{ title }}</h2>
        <div class="table-meta">已选 {{ selectedCount }} 项</div>
      </div>
      <div class="actions">
        <button class="button" @click="openAdd">新增</button>
        <button class="button secondary" @click="toggleMulti">
          {{ multiSelect ? '单选' : '多选' }}
        </button>
        <button class="button secondary" @click="openEdit" :disabled="selectedCount !== 1">
          编辑
        </button>
        <button class="button danger" @click="removeSelected" :disabled="selectedCount === 0">
          删除
        </button>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="list-table">
        <thead>
          <tr>
            <th class="col-index">序号</th>
            <th>内容</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, index) in modelValue"
            :key="index"
            :class="{ selected: isSelected(index) }"
            @mousedown="onRowMouseDown(index, $event)"
            @mouseenter="onRowMouseEnter(index)"
          >
            <td class="col-index">{{ index + 1 }}</td>
            <td>{{ itemDisplay(item) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!modelValue || modelValue.length === 0" class="empty">
        暂无数据
      </div>
    </div>

    <div class="table-footer">
      <div class="actions">
        <button class="button secondary" @click="exportYaml">导出</button>
        <button class="button secondary" @click="triggerImport">导入</button>
        <input
          ref="fileInput"
          type="file"
          accept=".yaml,.yml"
          class="hidden-input"
          @change="handleImport"
        />
      </div>
    </div>

    <div v-if="editOpen" class="modal-backdrop" @click.self="closeEdit">
      <div class="modal">
        <h3>编辑条目</h3>
        <input v-model="editValue" class="modal-input" />
        <div class="actions">
          <button class="button secondary" @click="closeEdit">取消</button>
          <button class="button" @click="applyEdit">保存</button>
        </div>
      </div>
    </div>

    <div v-if="addOpen" class="modal-backdrop" @click.self="closeAdd">
      <div class="modal">
        <h3>新增条目</h3>
        <textarea
          v-model="addValue"
          class="modal-textarea"
          placeholder="每行一条，支持批量新增"
        ></textarea>
        <div class="actions">
          <button class="button secondary" @click="closeAdd">取消</button>
          <button class="button" @click="applyAdd">新增</button>
        </div>
      </div>
    </div>

    <div v-if="messageOpen" class="modal-backdrop" @click.self="closeMessage">
      <div class="modal">
        <h3>提示</h3>
        <p class="modal-text">{{ messageText }}</p>
        <div class="actions">
          <button class="button" @click="closeMessage">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import yaml from 'js-yaml'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: ''
  },
  tableKey: {
    type: String,
    default: ''
  },
  itemType: {
    type: String,
    default: 'string'
  }
})

const emit = defineEmits(['update:modelValue'])

const selectedIndices = ref(new Set())
const multiSelect = ref(false)
const dragging = ref(false)
const anchorIndex = ref(null)
const editOpen = ref(false)
const editValue = ref('')
const editIndex = ref(null)
const addOpen = ref(false)
const addValue = ref('')
const fileInput = ref(null)
const messageOpen = ref(false)
const messageText = ref('')

const selectedCount = computed(() => selectedIndices.value.size)

function itemDisplay(item) {
  if (item === null || item === undefined) return ''
  return String(item)
}

function toggleMulti() {
  multiSelect.value = !multiSelect.value
  if (!multiSelect.value && selectedIndices.value.size > 1) {
    const first = selectedIndices.value.values().next().value
    selectedIndices.value = new Set([first])
  }
}

function isSelected(index) {
  return selectedIndices.value.has(index)
}

function setSelected(indices) {
  selectedIndices.value = new Set(indices)
}

function onRowMouseDown(index, event) {
  if (event.button !== 0) return
  if (multiSelect.value && (event.ctrlKey || event.metaKey)) {
    const next = new Set(selectedIndices.value)
    if (next.has(index)) {
      next.delete(index)
    } else {
      next.add(index)
    }
    selectedIndices.value = next
  } else {
    setSelected([index])
  }
  anchorIndex.value = index
  dragging.value = multiSelect.value
  window.addEventListener('mouseup', stopDragging)
}

function onRowMouseEnter(index) {
  if (!dragging.value || !multiSelect.value || anchorIndex.value === null) return
  const start = Math.min(anchorIndex.value, index)
  const end = Math.max(anchorIndex.value, index)
  const range = []
  for (let i = start; i <= end; i += 1) {
    range.push(i)
  }
  setSelected(range)
}

function stopDragging() {
  dragging.value = false
  window.removeEventListener('mouseup', stopDragging)
}

onBeforeUnmount(() => {
  window.removeEventListener('mouseup', stopDragging)
})

function removeSelected() {
  if (selectedIndices.value.size === 0) return
  const next = props.modelValue.filter((_, index) => !selectedIndices.value.has(index))
  emit('update:modelValue', next)
  selectedIndices.value = new Set()
}

function openEdit() {
  if (selectedIndices.value.size !== 1) return
  const index = selectedIndices.value.values().next().value
  editIndex.value = index
  editValue.value = itemDisplay(props.modelValue[index])
  editOpen.value = true
}

function openAdd() {
  addValue.value = ''
  addOpen.value = true
}

function closeEdit() {
  editOpen.value = false
  editValue.value = ''
  editIndex.value = null
}

function closeAdd() {
  addOpen.value = false
  addValue.value = ''
}

function applyEdit() {
  const index = editIndex.value
  if (index === null || index === undefined) return
  const original = props.modelValue[index]
  let nextValue = editValue.value
  if (typeof original === 'number') {
    const num = Number(nextValue)
    nextValue = Number.isNaN(num) ? original : num
  }
  const next = [...props.modelValue]
  next[index] = nextValue
  emit('update:modelValue', next)
  closeEdit()
}

function parseLine(line) {
  const trimmed = line.trim()
  if (!trimmed) return null
  if (props.itemType === 'number') {
    const num = Number(trimmed)
    if (Number.isNaN(num)) return undefined
    return num
  }
  return trimmed
}

function applyAdd() {
  const lines = addValue.value.split(/\r?\n/)
  const next = [...(props.modelValue || [])]
  const parsed = []
  for (const line of lines) {
    const value = parseLine(line)
    if (value === null) continue
    if (value === undefined) {
      showMessage('新增失败：存在无效数字。')
      return
    }
    parsed.push(value)
  }
  if (parsed.length === 0) {
    showMessage('新增失败：请输入内容。')
    return
  }
  emit('update:modelValue', [...next, ...parsed])
  selectedIndices.value = new Set()
  closeAdd()
}

function triggerImport() {
  if (fileInput.value) {
    fileInput.value.value = ''
    fileInput.value.click()
  }
}

function showMessage(text) {
  messageText.value = text
  messageOpen.value = true
}

function closeMessage() {
  messageOpen.value = false
  messageText.value = ''
}

function handleImport(event) {
  const file = event.target.files && event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    try {
      const data = yaml.load(reader.result)
      if (!data || typeof data !== 'object') {
        showMessage('导入失败：YAML 内容无效。')
        return
      }
      if (data.table !== props.tableKey) {
        showMessage('导入失败：表信息不匹配。')
        return
      }
      if (!Array.isArray(data.items)) {
        showMessage('导入失败：items 必须是数组。')
        return
      }
      emit('update:modelValue', data.items)
      selectedIndices.value = new Set()
      showMessage('导入成功。')
    } catch (error) {
      showMessage(`导入失败：${error.message}`)
    }
  }
  reader.readAsText(file)
}

function exportYaml() {
  const payload = {
    uuid: crypto.randomUUID(),
    table: props.tableKey,
    exported_at: new Date().toISOString(),
    items: props.modelValue || []
  }
  const text = yaml.dump(payload, { lineWidth: 120 })
  const blob = new Blob([text], { type: 'text/yaml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${props.tableKey || 'table'}.yaml`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>
