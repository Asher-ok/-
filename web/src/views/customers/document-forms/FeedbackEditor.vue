<template>
  <div class="feedback-editor">
    <el-form :model="form" ref="formRef" label-width="140px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('customerDoc.feedbackRating')">
        <el-rate v-model="form.feedback_rating" :max="5" />
      </el-form-item>
      <el-form-item :label="$t('customerDoc.ndisComplaintHotline')">
        <span class="hotline-text">{{ $t('customerDoc.ndisComplaintHotlineValue') }}</span>
        <a :href="'tel:1800035544'" class="hotline-link">1800 035 544</a>
      </el-form-item>
      <el-form-item :label="$t('customerDoc.formData')">
        <el-input v-model="form.form_data_json" type="textarea" :rows="3" :placeholder="$t('customerDoc.formDataPlaceholder')" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'FeedbackEditor' })
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  doc: { type: Object, required: true },
  customerId: { type: String, required: true }
})

const formRef = ref(null)
const form = ref({
  name: '',
  feedback_rating: 0,
  form_data_json: ''
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    form.value.feedback_rating = doc.form_data?.rating ?? 0
    let json = ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      try {
        const copy = { ...doc.form_data }
        delete copy.rating
        json = JSON.stringify(copy, null, 2)
      } catch {
        json = ''
      }
    }
    form.value.form_data_json = json
  },
  { immediate: true }
)

const getFormData = () => {
  const formData = { rating: form.value.feedback_rating }
  if (form.value.form_data_json?.trim()) {
    try {
      Object.assign(formData, JSON.parse(form.value.form_data_json))
    } catch {}
  }
  return {
    name: form.value.name,
    form_data: formData
  }
}

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>

<style scoped>
.hotline-text { margin-right: 8px; }
.hotline-link { color: #409eff; }
</style>
