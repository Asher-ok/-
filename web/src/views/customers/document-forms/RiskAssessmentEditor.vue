<template>
  <div class="risk-assessment-editor">
    <el-form :model="form" ref="formRef" label-width="200px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('riskAssessment.dimensions') }}</el-divider>
      <el-form-item v-for="(dim, key) in dimensions" :key="key" :label="dim.label">
        <el-radio-group v-model="form.dimensions[key]">
          <el-radio :label="1">{{ $t('riskAssessment.level1') }}</el-radio>
          <el-radio :label="2">{{ $t('riskAssessment.level2') }}</el-radio>
          <el-radio :label="3">{{ $t('riskAssessment.level3') }}</el-radio>
          <el-radio :label="4">{{ $t('riskAssessment.level4') }}</el-radio>
          <el-radio :label="5">{{ $t('riskAssessment.level5') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-divider content-position="left">{{ $t('riskAssessment.consequenceMatrix') }}</el-divider>
      <el-alert v-if="hasExtreme" type="error" :title="$t('riskAssessment.hasExtreme')" show-icon />
      <el-form-item v-if="hasExtreme" :label="$t('riskAssessment.actionPlan')" required>
        <el-input v-model="form.action_plan" type="textarea" :rows="4" :placeholder="$t('riskAssessment.actionPlanPlaceholder')" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'RiskAssessmentEditor' })
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  doc: { type: Object, required: true },
  customerId: { type: String, required: true }
})

const DIMENSION_KEYS = ['swallowing', 'mobility', 'bsp', 'manual_handling']

const dimensions = computed(() => ({
  swallowing: { label: t('riskAssessment.swallowing') },
  mobility: { label: t('riskAssessment.mobility') },
  bsp: { label: t('riskAssessment.bsp') },
  manual_handling: { label: t('riskAssessment.manualHandling') }
}))

const formRef = ref(null)
const emptyDimensions = () => Object.fromEntries(DIMENSION_KEYS.map((k) => [k, 1]))

const form = ref({
  name: '',
  dimensions: emptyDimensions(),
  action_plan: ''
})

const hasExtreme = computed(() => {
  const d = form.value.dimensions
  return Object.values(d).some((v) => v === 5)
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.action_plan = doc.form_data.action_plan ?? ''
      if (doc.form_data.dimensions) {
        const base = emptyDimensions()
        for (const k of DIMENSION_KEYS) {
          const v = doc.form_data.dimensions[k]
          base[k] = v != null && v >= 1 && v <= 5 ? Number(v) : 1
        }
        form.value.dimensions = base
      }
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    dimensions: form.value.dimensions,
    action_plan: form.value.action_plan || null
  }
})

const validate = async () => {
  if (hasExtreme.value && !form.value.action_plan?.trim()) {
    throw new Error(t('riskAssessment.actionPlanRequired'))
  }
  return getFormData()
}

defineExpose({ validate, getFormData })
</script>
