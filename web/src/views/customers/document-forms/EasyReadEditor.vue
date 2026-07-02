<template>
  <div class="easy-read-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('easyRead.viewMode')">
        <el-radio-group v-model="form.view_mode">
          <el-radio value="standard">{{ $t('easyRead.standardView') }}</el-radio>
          <el-radio value="easy_read">{{ $t('easyRead.easyReadView') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-divider content-position="left">{{ $t('easyRead.complaintEasyRead') }}</el-divider>
      <el-form-item :label="$t('easyRead.complaintEasyRead')">
        <el-input v-model="form.complaint_easy_read" type="textarea" :rows="4" :placeholder="$t('easyRead.complaintPlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('easyRead.incidentEasyRead') }}</el-divider>
      <el-form-item :label="$t('easyRead.incidentEasyRead')">
        <el-input v-model="form.incident_easy_read" type="textarea" :rows="4" :placeholder="$t('easyRead.incidentPlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('easyRead.agreementEasyRead') }}</el-divider>
      <el-form-item :label="$t('easyRead.agreementEasyRead')">
        <el-input v-model="form.agreement_easy_read" type="textarea" :rows="4" :placeholder="$t('easyRead.agreementPlaceholder')" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'EasyReadEditor' })
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
  view_mode: 'standard',
  complaint_easy_read: '',
  incident_easy_read: '',
  agreement_easy_read: ''
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.view_mode = doc.form_data.view_mode || 'standard'
      form.value.complaint_easy_read = doc.form_data.complaint_easy_read ?? ''
      form.value.incident_easy_read = doc.form_data.incident_easy_read ?? ''
      form.value.agreement_easy_read = doc.form_data.agreement_easy_read ?? ''
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    view_mode: form.value.view_mode,
    complaint_easy_read: form.value.complaint_easy_read || null,
    incident_easy_read: form.value.incident_easy_read || null,
    agreement_easy_read: form.value.agreement_easy_read || null
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
