<template>
  <div class="generic-form-editor">
    <el-form :model="form" ref="formRef" label-width="140px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('customerDoc.formData')">
        <el-input
          v-model="form.form_data_json"
          type="textarea"
          :rows="12"
          :placeholder="$t('customerDoc.formDataPlaceholder')"
        />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'GenericFormEditor' })
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  doc: { type: Object, required: true },
  customerId: { type: String, required: true }
})

const emit = defineEmits(['saved'])

const formRef = ref(null)
const form = ref({
  name: '',
  form_data_json: ''
})

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    let json = ''
    if (doc.form_data != null) {
      try {
        json = typeof doc.form_data === 'string'
          ? doc.form_data
          : JSON.stringify(doc.form_data, null, 2)
      } catch {
        json = ''
      }
    }
    form.value.form_data_json = json
  },
  { immediate: true }
)

const getFormData = () => {
  const data = { name: form.value.name }
  if (form.value.form_data_json?.trim()) {
    try {
      data.form_data = JSON.parse(form.value.form_data_json)
    } catch {
      return null
    }
  } else {
    data.form_data = {}
  }
  return data
}

const validate = async () => {
  const data = getFormData()
  if (!data) throw new Error(t('customerDoc.formDataInvalid'))
  return data
}

defineExpose({ validate, getFormData })
</script>
