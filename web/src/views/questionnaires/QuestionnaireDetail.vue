<template>
  <div class="questionnaire-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ $t('questionnaireDetail.title') }}</span>
          <el-button @click="$router.back()">{{ $t('questionnaireDetail.return') }}</el-button>
        </div>
      </template>
      
      <el-form :model="form" label-width="100px">
        <el-form-item :label="$t('questionnaireDetail.titleLabel')">
          <div class="localized-field">
            <el-input
              v-model="form.title_i18n.zh"
              :placeholder="$t('questionnaireDetail.questionnaireTitleZhPlaceholder')"
            />
            <el-input
              v-model="form.title_i18n.en"
              :placeholder="$t('questionnaireDetail.questionnaireTitleEnPlaceholder')"
            />
          </div>
        </el-form-item>
        <el-form-item :label="$t('questionnaireDetail.description')">
          <div class="localized-field">
            <el-input
              v-model="form.description_i18n.zh"
              type="textarea"
              :placeholder="$t('questionnaireDetail.questionnaireDescriptionZhPlaceholder')"
            />
            <el-input
              v-model="form.description_i18n.en"
              type="textarea"
              :placeholder="$t('questionnaireDetail.questionnaireDescriptionEnPlaceholder')"
            />
          </div>
        </el-form-item>
        <el-form-item :label="$t('questionnaireDetail.status')">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      
      <el-divider>{{ $t('questionnaireDetail.questionList') }}</el-divider>
      
      <div v-for="(question, index) in form.questions" :key="question.id || index" class="question-item">
        <el-card>
          <div class="question-header">
            <span>{{ $t('questionnaireDetail.question') }} {{ index + 1 }}</span>
            <el-button type="danger" size="small" @click="handleDeleteQuestion(index)">{{ $t('questionnaireDetail.delete') }}</el-button>
          </div>
          <el-form :model="question" label-width="100px">
            <el-form-item :label="$t('questionnaireDetail.titleLabel')">
              <div class="localized-field">
                <el-input
                  v-model="question.title_i18n.zh"
                  :placeholder="$t('questionnaireDetail.titleZhPlaceholder')"
                />
                <el-input
                  v-model="question.title_i18n.en"
                  :placeholder="$t('questionnaireDetail.titleEnPlaceholder')"
                />
              </div>
            </el-form-item>
            <el-form-item :label="$t('questionnaireDetail.type')">
              <el-select v-model="question.type">
                <el-option :label="$t('questionnaireDetail.singleChoice')" value="single_choice" />
                <el-option :label="$t('questionnaireDetail.multipleChoice')" value="multiple_choice" />
                <el-option :label="$t('questionnaireDetail.text')" value="text" />
                <el-option :label="$t('questionnaireDetail.number')" value="number" />
                <el-option :label="$t('questionnaireDetail.date')" value="date" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('questionnaireDetail.required')">
              <el-switch v-model="question.required" />
            </el-form-item>
            <el-form-item v-if="isChoiceQuestion(question.type)" :label="$t('questionnaireDetail.options')">
              <div class="option-list">
                <div
                  v-for="(option, optionIndex) in question.options"
                  :key="option.id || optionIndex"
                  class="option-item"
                >
                  <div class="option-fields">
                    <el-input
                      v-model="option.text_i18n.zh"
                      :placeholder="$t('questionnaireDetail.optionTextZhPlaceholder')"
                    />
                    <el-input
                      v-model="option.text_i18n.en"
                      :placeholder="$t('questionnaireDetail.optionTextEnPlaceholder')"
                    />
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    plain
                    @click="removeOption(question, optionIndex)"
                  >
                    {{ $t('questionnaireDetail.delete') }}
                  </el-button>
                </div>
                <el-button type="primary" plain size="small" @click="addOption(question)">
                  {{ $t('questionnaireDetail.addOption') }}
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
      
      <el-button type="primary" @click="handleAddQuestion" style="margin-top: 20px">
        <el-icon><Plus /></el-icon>
        {{ $t('questionnaireDetail.addQuestion') }}
      </el-button>
      
      <div style="margin-top: 20px">
        <el-button @click="$router.back()">{{ $t('questionnaireDetail.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave">{{ $t('questionnaireDetail.save') }}</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getQuestionnaire, updateQuestionnaire, createQuestionnaire } from '@/api/questionnaires'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const questionnaireId = route.params.id
const loading = ref(false)

const form = reactive({
  title: '',
  title_i18n: { zh: '', en: '' },
  description: '',
  description_i18n: { zh: '', en: '' },
  is_active: true,
  questions: []
})

const normalizeString = (value) => {
  if (value == null) return ''
  return String(value).trim()
}

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

const pickPrimaryText = (i18nValue, fallback = '') => {
  const normalized = normalizeI18nText(i18nValue)
  return normalized.zh || normalized.en || normalizeString(fallback)
}

const normalizeOption = (option, idx) => {
  if (option == null) return null
  if (typeof option === 'string' || typeof option === 'number') {
    const text = normalizeString(option)
    if (!text) return null
    return {
      id: `opt${idx + 1}`,
      text,
      text_i18n: normalizeI18nText(null, text)
    }
  }
  if (typeof option !== 'object') return null

  const textI18n = normalizeI18nText(
    option.text_i18n || {
      zh: option.text_zh || option.label_zh,
      en: option.text_en || option.label_en
    },
    option.text ?? option.label ?? option.value ?? option.name ?? ''
  )
  const text = pickPrimaryText(textI18n, option.text ?? option.label ?? option.value ?? option.name ?? '')
  if (!text) return null
  return {
    id: option.id ?? `opt${idx + 1}`,
    text,
    text_i18n: textI18n
  }
}

const loadQuestionnaire = async () => {
  if (questionnaireId === 'new') return
  
  loading.value = true
  try {
    const data = await getQuestionnaire(questionnaireId)
    Object.assign(form, data)
    form.title_i18n = normalizeI18nText(data?.title_i18n, data?.title)
    form.description_i18n = normalizeI18nText(data?.description_i18n, data?.description)
    form.title = pickPrimaryText(form.title_i18n, data?.title)
    form.description = pickPrimaryText(form.description_i18n, data?.description)
    const rawQuestions =
      Array.isArray(data?.questions) ? data.questions :
      Array.isArray(data?.questionList) ? data.questionList :
      Array.isArray(data?.question_list) ? data.question_list :
      Array.isArray(data?.items) ? data.items : []
    form.questions = rawQuestions.map((question) => ({
      ...question,
      title_i18n: normalizeI18nText(question.title_i18n, question.title),
      title: pickPrimaryText(question.title_i18n, question.title),
      options: Array.isArray(question.options)
        ? question.options
            .map((opt, idx) => normalizeOption(opt, idx))
            .filter((o) => o && normalizeString(o.text))
        : []
    }))
  } catch (error) {
    ElMessage.error(t('questionnaireDetail.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleAddQuestion = () => {
  form.questions.push({
    title: '',
    title_i18n: { zh: '', en: '' },
    type: 'single_choice',
    required: false,
    options: [],
    placeholder: '',
    hint: ''
  })
}

const handleDeleteQuestion = (index) => {
  form.questions.splice(index, 1)
}

const isChoiceQuestion = (type) => type === 'single_choice' || type === 'multiple_choice'

const addOption = (question) => {
  if (!Array.isArray(question.options)) {
    question.options = []
  }
  const nextIndex = question.options.length + 1
  question.options.push({
    id: `opt${nextIndex}`,
    text: '',
    text_i18n: { zh: '', en: '' }
  })
}

const removeOption = (question, optionIndex) => {
  if (!Array.isArray(question.options)) return
  question.options.splice(optionIndex, 1)
}

const handleSave = async () => {
  try {
    if (questionnaireId === 'new') {
      await createQuestionnaire(form)
      ElMessage.success(t('questionnaireDetail.createSuccess'))
    } else {
      await updateQuestionnaire(questionnaireId, form)
      ElMessage.success(t('questionnaireDetail.updateSuccess'))
    }
    router.push('/questionnaires')
  } catch (error) {
    ElMessage.error(t('questionnaireDetail.saveFailed'))
  }
}

onMounted(() => {
  loadQuestionnaire()
})
</script>

<style scoped>
.questionnaire-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.question-item {
  margin-bottom: 20px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.option-list {
  width: 100%;
}

.localized-field,
.option-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}
</style>
