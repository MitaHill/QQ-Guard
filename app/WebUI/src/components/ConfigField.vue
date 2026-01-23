<template>
  <div class="field">
    <label v-if="displayLabel && !hideLabel">{{ displayLabel }}</label>

    <div v-if="isArray">
      <div v-if="useTextarea">
        <textarea
          :value="arrayText"
          @input="updateFromTextarea"
          spellcheck="false"
        ></textarea>
      </div>
      <div v-else class="config-grid">
        <div v-for="(item, index) in modelValue" :key="index" class="field">
          <input
            v-if="arrayItemType === 'number'"
            type="number"
            :value="item"
            @input="updateArrayItem(index, $event.target.value)"
          />
          <input
            v-else-if="arrayItemType === 'boolean'"
            type="checkbox"
            :checked="item"
            @change="updateArrayItem(index, $event.target.checked)"
          />
          <input
            v-else
            type="text"
            :value="item"
            @input="updateArrayItem(index, $event.target.value)"
          />
          <button class="button secondary" @click="removeArrayItem(index)">移除</button>
        </div>
        <button class="button secondary" @click="addArrayItem">添加一项</button>
      </div>
    </div>

    <div v-else-if="isObject" class="nested">
      <ConfigField
        v-for="(value, key) in modelValue"
        :key="key"
        :field-key="key"
        :path="nextPath(key)"
        :label-map="labelMap"
        :model-value="value"
        @update:modelValue="updateObjectField(key, $event)"
      />
    </div>

    <div v-else>
      <input
        v-if="valueType === 'number'"
        type="number"
        :value="modelValue"
        @input="updatePrimitive($event.target.value)"
      />
      <input
        v-else-if="valueType === 'boolean'"
        type="checkbox"
        :checked="modelValue"
        @change="updatePrimitive($event.target.checked)"
      />
      <input
        v-else
        type="text"
        :value="modelValue"
        @input="updatePrimitive($event.target.value)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

defineOptions({ name: 'ConfigField' })

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, Array, Object],
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  labelMap: {
    type: Object,
    default: null
  },
  fieldKey: {
    type: String,
    default: ''
  },
  path: {
    type: String,
    default: ''
  },
  hideLabel: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isArray = computed(() => Array.isArray(props.modelValue))
const isObject = computed(() => props.modelValue && typeof props.modelValue === 'object' && !Array.isArray(props.modelValue))
const valueType = computed(() => typeof props.modelValue)

const arrayItemType = computed(() => {
  if (!isArray.value || props.modelValue.length === 0) return 'string'
  const first = props.modelValue[0]
  return typeof first
})

const useTextarea = computed(() => {
  if (!isArray.value) return false
  if (props.modelValue.length > 50) return true
  return arrayItemType.value === 'string' && props.modelValue.join('').length > 280
})

const displayLabel = computed(() => {
  if (props.label) return props.label
  const map = props.labelMap || {}
  if (props.path && map[props.path]) return map[props.path]
  if (props.fieldKey && map[props.fieldKey]) return map[props.fieldKey]
  return props.fieldKey
})

function nextPath(key) {
  if (!props.path) return key
  return `${props.path}.${key}`
}

const arrayText = computed(() => {
  if (!isArray.value) return ''
  return props.modelValue.map(String).join('\n')
})

function updateObjectField(key, value) {
  const next = { ...(props.modelValue || {}) }
  next[key] = value
  emit('update:modelValue', next)
}

function coerceValue(value, type) {
  if (type === 'number') {
    const num = Number(value)
    return Number.isNaN(num) ? 0 : num
  }
  if (type === 'boolean') {
    return value === true || value === 'true'
  }
  return value
}

function updatePrimitive(value) {
  emit('update:modelValue', coerceValue(value, valueType.value))
}

function updateArrayItem(index, value) {
  const next = [...props.modelValue]
  next[index] = coerceValue(value, arrayItemType.value)
  emit('update:modelValue', next)
}

function addArrayItem() {
  const next = [...props.modelValue]
  next.push(coerceValue('', arrayItemType.value))
  emit('update:modelValue', next)
}

function removeArrayItem(index) {
  const next = [...props.modelValue]
  next.splice(index, 1)
  emit('update:modelValue', next)
}

function updateFromTextarea(event) {
  const lines = event.target.value.split('\n').map(line => line.trim()).filter(Boolean)
  const next = lines.map(line => coerceValue(line, arrayItemType.value))
  emit('update:modelValue', next)
}
</script>
