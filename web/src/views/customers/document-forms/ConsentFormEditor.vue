<template>
  <div class="consent-form-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('consentForm.section1Title') }}</el-divider>
      <el-table :data="form.section1_rows" border>
        <el-table-column :label="$t('consentForm.serviceType')" width="140">
          <template #default="{ row }">
            <el-input v-model="row.service_type" size="small" :placeholder="$t('consentForm.serviceTypePlaceholder')" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('consentForm.orgName')" width="140">
          <template #default="{ row }">
            <el-input v-model="row.org" size="small" :placeholder="$t('consentForm.orgPlaceholder')" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('consentForm.infoType')" width="120">
          <template #default="{ row }">
            <el-select v-model="row.info_type" size="small" :placeholder="$t('consentForm.infoTypePlaceholder')" clearable style="width: 100%">
              <el-option :label="$t('consentForm.allInfo')" value="all" />
              <el-option :label="$t('consentForm.specificInfo')" value="specific" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column :label="$t('consentForm.purpose')" min-width="160">
          <template #default="{ row }">
            <el-input v-model="row.purpose" size="small" :placeholder="$t('consentForm.purposePlaceholder')" />
          </template>
        </el-table-column>
        <el-table-column width="60">
          <template #default="{ $index }">
            <el-button type="danger" size="small" link @click="removeSection1Row($index)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" plain size="small" @click="addSection1Row" style="margin-top: 8px">
        {{ $t('consentForm.addRow') }}
      </el-button>
      <el-divider content-position="left">{{ $t('consentForm.section2Title') }}</el-divider>
      <el-form-item :label="$t('consentForm.auditConsent')">
        <el-checkbox v-model="form.audit_consent">{{ $t('consentForm.auditConsentLabel') }}</el-checkbox>
      </el-form-item>
      <el-form-item :label="$t('consentForm.avConsent')">
        <el-checkbox v-model="form.av_consent">{{ $t('consentForm.avConsentLabel') }}</el-checkbox>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'ConsentFormEditor' })
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
  section1_rows: [{ service_type: '', org: '', info_type: '', purpose: '' }],
  audit_consent: false,
  av_consent: false
})

function addSection1Row() {
  form.value.section1_rows.push({ service_type: '', org: '', info_type: '', purpose: '' })
}

function removeSection1Row(index) {
  if (form.value.section1_rows.length > 1) {
    form.value.section1_rows.splice(index, 1)
  }
}

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.audit_consent = doc.form_data.audit_consent ?? false
      form.value.av_consent = doc.form_data.av_consent ?? false
      if (Array.isArray(doc.form_data.section1_rows) && doc.form_data.section1_rows.length > 0) {
        form.value.section1_rows = doc.form_data.section1_rows.map((r) => ({
          service_type: r.service_type ?? '',
          org: r.org ?? '',
          info_type: r.info_type ?? '',
          purpose: r.purpose ?? ''
        }))
      }
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    section1_rows: form.value.section1_rows,
    audit_consent: form.value.audit_consent,
    av_consent: form.value.av_consent
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
