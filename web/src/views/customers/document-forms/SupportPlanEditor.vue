<template>
  <div class="support-plan-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('supportPlan.alarmPlan')">
        <el-input v-model="form.alarm_plan" type="textarea" :rows="4" :placeholder="$t('supportPlan.alarmPlanPlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('supportPlan.allergies')">
        <el-input v-model="form.allergies" type="textarea" :rows="3" :placeholder="$t('supportPlan.allergiesPlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('supportPlan.emergencyProfile')">
        <el-input v-model="form.emergency_profile" type="textarea" :rows="4" :placeholder="$t('supportPlan.emergencyProfilePlaceholder')" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'SupportPlanEditor' })
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
  alarm_plan: '',
  allergies: '',
  emergency_profile: ''
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.alarm_plan = doc.form_data.alarm_plan ?? ''
      form.value.allergies = doc.form_data.allergies ?? ''
      form.value.emergency_profile = doc.form_data.emergency_profile ?? ''
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    alarm_plan: form.value.alarm_plan || null,
    allergies: form.value.allergies || null,
    emergency_profile: form.value.emergency_profile || null
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
