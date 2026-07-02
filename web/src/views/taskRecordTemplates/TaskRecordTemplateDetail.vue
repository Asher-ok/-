<template>
  <div class="template-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ $t('taskRecordTemplateDetail.title') }}</span>
          <el-button @click="$router.back()">{{ $t('common.return') }}</el-button>
        </div>
      </template>

      <el-form :model="form" label-width="110px">
        <el-form-item :label="$t('taskRecordTemplateDetail.titleLabel')">
          <div class="localized-field">
            <el-input v-model="form.title_i18n.zh" :placeholder="$t('taskRecordTemplateDetail.titleZhPlaceholder')" />
            <el-input v-model="form.title_i18n.en" :placeholder="$t('taskRecordTemplateDetail.titleEnPlaceholder')" />
          </div>
        </el-form-item>
        <el-form-item :label="$t('taskRecordTemplateDetail.description')">
          <div class="localized-field">
            <el-input
              v-model="form.description_i18n.zh"
              type="textarea"
              :placeholder="$t('taskRecordTemplateDetail.descriptionZhPlaceholder')"
            />
            <el-input
              v-model="form.description_i18n.en"
              type="textarea"
              :placeholder="$t('taskRecordTemplateDetail.descriptionEnPlaceholder')"
            />
          </div>
        </el-form-item>
        <el-form-item :label="$t('taskRecordTemplateDetail.status')">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>

      <el-divider>{{ $t('taskRecordTemplateDetail.fieldList') }}</el-divider>

      <div v-for="(question, index) in form.questions" :key="question.id || index" class="question-item">
        <el-card>
          <div class="question-header">
            <span>{{ $t('taskRecordTemplateDetail.field') }} {{ index + 1 }}</span>
            <el-button type="danger" size="small" @click="handleDeleteQuestion(index)">{{ $t('common.delete') }}</el-button>
          </div>
          <el-form :model="question" label-width="110px">
            <el-form-item :label="$t('taskRecordTemplateDetail.fieldLabel')">
              <div class="localized-field">
                <el-input v-model="question.title_i18n.zh" :placeholder="$t('taskRecordTemplateDetail.fieldZhPlaceholder')" />
                <el-input v-model="question.title_i18n.en" :placeholder="$t('taskRecordTemplateDetail.fieldEnPlaceholder')" />
              </div>
            </el-form-item>
            <el-form-item :label="$t('taskRecordTemplateDetail.type')">
              <el-select v-model="question.type">
                <el-option :label="$t('taskRecordTemplateDetail.singleChoice')" value="single_choice" />
                <el-option :label="$t('taskRecordTemplateDetail.multipleChoice')" value="multiple_choice" />
                <el-option :label="$t('taskRecordTemplateDetail.checkbox')" value="checkbox" />
                <el-option :label="$t('taskRecordTemplateDetail.text')" value="text" />
                <el-option :label="$t('taskRecordTemplateDetail.number')" value="number" />
                <el-option :label="$t('taskRecordTemplateDetail.date')" value="date" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('taskRecordTemplateDetail.required')">
              <el-switch v-model="question.required" />
            </el-form-item>
            <el-form-item v-if="isChoiceQuestion(question.type)" :label="$t('taskRecordTemplateDetail.options')">
              <div class="option-list">
                <div v-for="(option, optionIndex) in question.options" :key="option.id || optionIndex" class="option-item">
                  <div class="option-fields">
                    <el-input v-model="option.text_i18n.zh" :placeholder="$t('taskRecordTemplateDetail.optionZhPlaceholder')" />
                    <el-input v-model="option.text_i18n.en" :placeholder="$t('taskRecordTemplateDetail.optionEnPlaceholder')" />
                  </div>
                  <el-button type="danger" size="small" plain @click="removeOption(question, optionIndex)">
                    {{ $t('common.delete') }}
                  </el-button>
                </div>
                <el-button type="primary" plain size="small" @click="addOption(question)">
                  {{ $t('taskRecordTemplateDetail.addOption') }}
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <el-button type="primary" @click="handleAddQuestion" style="margin-top: 20px">
        {{ $t('taskRecordTemplateDetail.addField') }}
      </el-button>

      <div style="margin-top: 20px">
        <el-button @click="$router.back()">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave">{{ $t('common.save') }}</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
defineOptions({ name: 'TaskRecordTemplateDetail' })
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTaskRecordTemplate, updateTaskRecordTemplate, createTaskRecordTemplate } from '@/api/taskRecordTemplates'

const route = useRoute()
const router = useRouter()
const templateId = route.params.id
const loading = ref(false)

const form = reactive({
  title_i18n: { zh: '', en: '' },
  description_i18n: { zh: '', en: '' },
  is_active: true,
  questions: []
})

const normalizeString = (value) => (value == null ? '' : String(value)).trim()
const normalizeI18nText = (value, fallback = '') => {
  const next = { zh: '', en: '' }
  if (value && typeof value === 'object') {
    next.zh = normalizeString(value.zh || value['zh-CN'] || value.cn)
    next.en = normalizeString(value.en || value['en-US'])
  }
  if (!next.zh && !next.en) {
    const base = normalizeString(fallback)
    if (base) next.zh = base
  }
  return next
}

const normalizeOption = (option, idx) => {
  const textI18n = normalizeI18nText(option?.text_i18n, option?.text || '')
  return {
    id: option?.id ?? `opt${idx + 1}`,
    text_i18n: textI18n
  }
}

const normalizeQuestion = (q, idx) => {
  const titleI18n = normalizeI18nText(q?.title_i18n, q?.title || '')
  return {
    id: q?.id ?? `q${idx + 1}`,
    title_i18n: titleI18n,
    type: q?.type || 'single_choice',
    required: !!q?.required,
    options: Array.isArray(q?.options) ? q.options.map((o, i) => normalizeOption(o, i)) : []
  }
}

const load = async () => {
  if (templateId === 'new') return
  loading.value = true
  try {
    const data = await getTaskRecordTemplate(templateId)
    form.title_i18n = normalizeI18nText(data?.title_i18n, data?.title)
    form.description_i18n = normalizeI18nText(data?.description_i18n, data?.description)
    form.is_active = data?.is_active !== false
    const questions = data?.schema_json?.questions || []
    form.questions = Array.isArray(questions) ? questions.map((q, idx) => normalizeQuestion(q, idx)) : []
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleAddQuestion = () => {
  const nextIndex = form.questions.length + 1
  form.questions.push({
    id: `q${nextIndex}`,
    title_i18n: { zh: '', en: '' },
    type: 'single_choice',
    required: false,
    options: []
  })
}

const handleDeleteQuestion = (index) => {
  form.questions.splice(index, 1)
}

const isChoiceQuestion = (type) => type === 'single_choice' || type === 'multiple_choice' || type === 'checkbox'

const addOption = (question) => {
  if (!Array.isArray(question.options)) question.options = []
  const nextIndex = question.options.length + 1
  question.options.push({ id: `opt${nextIndex}`, text_i18n: { zh: '', en: '' } })
}

const removeOption = (question, optionIndex) => {
  if (!Array.isArray(question.options)) return
  question.options.splice(optionIndex, 1)
}

const handleSave = async () => {
  const payload = {
    title: normalizeString(form.title_i18n.zh || form.title_i18n.en),
    title_i18n: form.title_i18n,
    description: normalizeString(form.description_i18n.zh || form.description_i18n.en),
    description_i18n: form.description_i18n,
    is_active: form.is_active,
    schema_json: { questions: form.questions },
    style_json: { preset: 'default' }
  }
  try {
    if (templateId === 'new') {
      await createTaskRecordTemplate(payload)
      ElMessage.success('创建成功')
    } else {
      await updateTaskRecordTemplate(templateId, payload)
      ElMessage.success('保存成功')
    }
    router.push('/task-record-templates/templates')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  }
}

load()
</script>

<style scoped>
.template-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.localized-field,
.option-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.question-item {
  margin-bottom: 16px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.option-list {
  width: 100%;
}

.option-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 10px;
}
</style>
