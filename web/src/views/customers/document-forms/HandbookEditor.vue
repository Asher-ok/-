<template>
  <div class="handbook-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('handbook.mission')">
        <el-input v-model="form.mission" type="textarea" :rows="3" :placeholder="$t('handbook.missionPlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('handbook.vision')">
        <el-input v-model="form.vision" type="textarea" :rows="3" :placeholder="$t('handbook.visionPlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('handbook.rights')">
        <el-input v-model="form.rights" type="textarea" :rows="4" :placeholder="$t('handbook.rightsPlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('handbook.revisionDate')">
        <el-date-picker v-model="form.revision_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" :placeholder="$t('handbook.revisionDatePlaceholder')" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'HandbookEditor' })
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
  mission: '',
  vision: '',
  rights: '',
  revision_date: ''
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.mission = doc.form_data.mission ?? ''
      form.value.vision = doc.form_data.vision ?? ''
      form.value.rights = doc.form_data.rights ?? ''
      form.value.revision_date = doc.form_data.revision_date ?? ''
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    mission: form.value.mission || null,
    vision: form.value.vision || null,
    rights: form.value.rights || null,
    revision_date: form.value.revision_date || null
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
