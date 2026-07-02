<template>
  <div class="exit-form-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('exitForm.endOfServiceDate')">
        <el-date-picker v-model="form.end_of_service_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" :placeholder="$t('exitForm.endOfServiceDatePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('exitForm.gpNotified')">
        <el-checkbox v-model="form.gp_notified">{{ $t('exitForm.gpNotifiedLabel') }}</el-checkbox>
      </el-form-item>
      <el-form-item :label="$t('exitForm.equipmentRetrieved')">
        <el-select v-model="form.equipment_retrieved" multiple filterable allow-create :placeholder="$t('exitForm.equipmentRetrievedPlaceholder')" style="width: 100%" />
      </el-form-item>
      <el-form-item :label="$t('exitForm.referralContacts')">
        <el-input v-model="form.referral_contacts" type="textarea" :rows="4" :placeholder="$t('exitForm.referralContactsPlaceholder')" />
      </el-form-item>
      <el-form-item v-if="form.end_of_service_date" :label="$t('exitForm.archiveUntil')">
        <el-input :model-value="archiveUntilDisplay" disabled />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'ExitFormEditor' })
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  doc: { type: Object, required: true },
  customerId: { type: String, required: true }
})

const formRef = ref(null)
const form = ref({
  name: '',
  end_of_service_date: '',
  gp_notified: false,
  equipment_retrieved: [],
  referral_contacts: ''
})

function addYears(dateStr, years) {
  if (!dateStr) return null
  const d = new Date(dateStr)
  d.setFullYear(d.getFullYear() + years)
  return d.toISOString().split('T')[0]
}

const archiveUntilDisplay = computed(() => {
  const computedVal = addYears(form.value.end_of_service_date, 7)
  return computedVal ? `${computedVal} (${t('exitForm.archiveNote')})` : ''
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.end_of_service_date = doc.form_data.end_of_service_date ?? ''
      form.value.gp_notified = doc.form_data.gp_notified ?? false
      form.value.equipment_retrieved = Array.isArray(doc.form_data.equipment_retrieved) ? doc.form_data.equipment_retrieved : []
      form.value.referral_contacts = doc.form_data.referral_contacts ?? ''
    }
  },
  { immediate: true }
)

const getFormData = () => {
  const archive_until = addYears(form.value.end_of_service_date, 7)
  return {
    name: form.value.name,
    form_data: {
      end_of_service_date: form.value.end_of_service_date || null,
      gp_notified: form.value.gp_notified,
      equipment_retrieved: form.value.equipment_retrieved,
      referral_contacts: form.value.referral_contacts || null,
      archive_until
    }
  }
}

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
