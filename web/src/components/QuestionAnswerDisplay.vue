<template>
  <div class="qa-list">
    <div v-for="item in questionAnswerList" :key="item.id" class="qa-item">
      <div class="qa-question">
        {{ item.title }}
        <span class="qa-meta">（{{ item.typeLabel }}{{ item.required ? $t('questionnaireSubmissions.required') : '' }}）</span>
      </div>
      <div v-if="item.isChoice" class="qa-options">
        <el-checkbox
          v-for="option in item.options"
          :key="option.id"
          :model-value="option.selected"
          disabled
          class="qa-option"
        >
          {{ option.text }}
        </el-checkbox>
      </div>
      <div v-else class="qa-answer">{{ item.answer || '—' }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

defineOptions({ name: 'QuestionAnswerDisplay' })

const props = defineProps({
  detail: {
    type: Object,
    default: null
  }
})

const { t, locale } = useI18n()

const questionAnswerList = computed(() => {
  if (!props.detail) return []
  const questions = Array.isArray(props.detail.questions) ? props.detail.questions : []
  const answers = props.detail.answers || {}
  return questions.map((question) => {
    const answerValue = answers[question.id]
    const answer = mapAnswer(question, answerValue)
    const options = buildOptions(question, answerValue)
    return {
      id: question.id,
      title: resolveLocalizedText(question.title_i18n, question.title),
      required: question.required,
      typeLabel: getTypeLabel(question.type),
      answer,
      isChoice: question.type === 'single_choice' || question.type === 'multiple_choice',
      options
    }
  })
})

function getTypeLabel(type) {
  const map = {
    single_choice: t('questionnaireSubmissions.singleChoice'),
    multiple_choice: t('questionnaireSubmissions.multipleChoice'),
    text: t('questionnaireSubmissions.text'),
    number: t('questionnaireSubmissions.number'),
    date: t('questionnaireSubmissions.date')
  }
  return map[type] || type
}

function resolveLocalizedText(i18nValue, fallback = '') {
  const lang = String(locale.value || 'zh').toLowerCase().startsWith('en') ? 'en' : 'zh'
  if (i18nValue && typeof i18nValue === 'object') {
    const direct = String(i18nValue[lang] || '').trim()
    const alternate = String(i18nValue[lang === 'zh' ? 'en' : 'zh'] || '').trim()
    if (direct) return direct
    if (alternate) return alternate
  }
  return String(fallback || '').trim()
}

function mapAnswer(question, value) {
  if (value === null || value === undefined) return ''
  const options = Array.isArray(question.options) ? question.options : []
  const optionMap = {}
  options.forEach((option) => {
    const text = resolveLocalizedText(option.text_i18n, option.text || option.label || option.value || '')
    if (option.id) optionMap[option.id] = text
    if (text) optionMap[text] = text
  })

  if (question.type === 'multiple_choice') {
    if (Array.isArray(value)) {
      return value.map((item) => optionMap[item] || item).join('，')
    }
    return optionMap[value] || value
  }

  if (question.type === 'single_choice') {
    return optionMap[value] || value
  }

  return String(value)
}

function buildOptions(question, value) {
  const options = Array.isArray(question.options) ? question.options : []
  const selectedSet = new Set()
  if (question.type === 'multiple_choice') {
    if (Array.isArray(value)) {
      value.forEach((item) => selectedSet.add(String(item)))
    } else if (value !== undefined && value !== null) {
      selectedSet.add(String(value))
    }
  } else if (question.type === 'single_choice') {
    if (value !== undefined && value !== null) {
      selectedSet.add(String(value))
    }
  }

  return options.map((option, index) => {
    const id = option.id || `opt_${index + 1}`
    const text = resolveLocalizedText(option.text_i18n, option.text || option.label || option.value || '')
    const selected = selectedSet.has(String(option.id)) || selectedSet.has(String(text))
    return { id, text, selected }
  })
}
</script>

<style scoped>
.qa-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-item {
  background: var(--el-fill-color-light);
  padding: 12px;
  border-radius: 6px;
}

.qa-question {
  font-weight: 600;
  margin-bottom: 6px;
}

.qa-meta {
  font-weight: normal;
  color: var(--el-text-color-secondary);
}

.qa-options {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.qa-option {
  color: var(--el-text-color-primary);
}

.qa-answer {
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
}
</style>
