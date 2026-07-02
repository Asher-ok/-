<template>
  <div class="intake-form-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('customer.identitySection') }}</el-divider>
      <el-form-item :label="$t('customer.aboriginalTorresStraitLabel')">
        <el-checkbox v-model="form.aboriginal_torres_strait">{{ $t('customer.aboriginalTorresStraitLabel') }}</el-checkbox>
      </el-form-item>
      <el-divider content-position="left">{{ $t('customer.fundingSection') }}</el-divider>
      <el-form-item :label="$t('customer.ndisFundingType')">
        <el-select v-model="form.ndis_funding_type" :placeholder="$t('customer.selectNdisFundingType')" clearable style="width: 100%">
          <el-option :label="$t('customer.ndisManaged')" value="NDIS Managed" />
          <el-option :label="$t('customer.selfManaged')" value="Self-Managed" />
          <el-option :label="$t('customer.planManaged')" value="Plan Managed" />
        </el-select>
      </el-form-item>
      <el-divider content-position="left">{{ $t('customer.medicareSection') }}</el-divider>
      <el-form-item :label="$t('customer.medicareNumber')">
        <el-input v-model="form.medicare_number" :placeholder="$t('customer.medicareNumber')" />
      </el-form-item>
      <el-form-item :label="$t('customer.medicareExpiry')">
        <el-date-picker v-model="form.medicare_expiry" type="date" :placeholder="$t('customer.selectMedicareExpiry')" value-format="YYYY-MM-DD" style="width: 100%" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('customer.privateHealthSection') }}</el-divider>
      <el-form-item :label="$t('customer.privateHealthFund')">
        <el-input v-model="form.private_health_fund" :placeholder="$t('customer.privateHealthFund')" />
      </el-form-item>
      <el-form-item :label="$t('customer.privatePolicyNumber')">
        <el-input v-model="form.private_policy_number" :placeholder="$t('customer.privatePolicyNumber')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('customer.invoiceReceiverSection') }}</el-divider>
      <el-form-item :label="$t('customer.invoiceReceiverName')">
        <el-input v-model="form.invoice_receiver_name" :placeholder="$t('customer.invoiceReceiverName')" />
      </el-form-item>
      <el-form-item :label="$t('customer.invoiceReceiverPhone')">
        <el-input v-model="form.invoice_receiver_phone" :placeholder="$t('customer.invoiceReceiverPhone')" />
      </el-form-item>
      <el-form-item :label="$t('customer.invoiceReceiverEmail')">
        <el-input v-model="form.invoice_receiver_email" :placeholder="$t('customer.invoiceReceiverEmail')" />
      </el-form-item>
      <el-form-item :label="$t('customer.invoiceReceiverAddress')">
        <el-input v-model="form.invoice_receiver_address" type="textarea" :rows="2" :placeholder="$t('customer.invoiceReceiverAddress')" />
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'IntakeFormEditor' })
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCustomer } from '@/api/customers'

const { t } = useI18n()
const props = defineProps({
  doc: { type: Object, required: true },
  customerId: { type: String, required: true }
})

const formRef = ref(null)
const form = ref({
  name: '',
  aboriginal_torres_strait: false,
  ndis_funding_type: '',
  medicare_number: '',
  medicare_expiry: '',
  private_health_fund: '',
  private_policy_number: '',
  invoice_receiver_name: '',
  invoice_receiver_phone: '',
  invoice_receiver_email: '',
  invoice_receiver_address: ''
})

function applyFormData(data) {
  if (!data || typeof data !== 'object') return
  form.value.aboriginal_torres_strait = data.aboriginal_torres_strait ?? false
  form.value.ndis_funding_type = data.ndis_funding_type ?? ''
  form.value.medicare_number = data.medicare_number ?? ''
  form.value.medicare_expiry = data.medicare_expiry ?? ''
  form.value.private_health_fund = data.private_health_fund ?? ''
  form.value.private_policy_number = data.private_policy_number ?? ''
  form.value.invoice_receiver_name = data.invoice_receiver_name ?? ''
  form.value.invoice_receiver_phone = data.invoice_receiver_phone ?? ''
  form.value.invoice_receiver_email = data.invoice_receiver_email ?? ''
  form.value.invoice_receiver_address = data.invoice_receiver_address ?? ''
}

function applyFromCustomer(c) {
  if (!c) return
  form.value.aboriginal_torres_strait = c.aboriginal_torres_strait ?? false
  form.value.ndis_funding_type = c.ndis_funding_type ?? ''
  form.value.medicare_number = c.medicare_number ?? ''
  form.value.medicare_expiry = c.medicare_expiry ?? ''
  form.value.private_health_fund = c.private_health_fund ?? ''
  form.value.private_policy_number = c.private_policy_number ?? ''
  form.value.invoice_receiver_name = c.invoice_receiver_name ?? ''
  form.value.invoice_receiver_phone = c.invoice_receiver_phone ?? ''
  form.value.invoice_receiver_email = c.invoice_receiver_email ?? ''
  form.value.invoice_receiver_address = c.invoice_receiver_address ?? ''
}

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      applyFormData(doc.form_data)
    }
  },
  { immediate: true }
)

onMounted(async () => {
  if (props.doc?.form_data && typeof props.doc.form_data === 'object' && Object.keys(props.doc.form_data).length > 0) {
    return
  }
  try {
    const customer = await getCustomer(props.customerId)
    applyFromCustomer(customer)
  } catch {}
})

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    aboriginal_torres_strait: form.value.aboriginal_torres_strait,
    ndis_funding_type: form.value.ndis_funding_type || null,
    medicare_number: form.value.medicare_number || null,
    medicare_expiry: form.value.medicare_expiry || null,
    private_health_fund: form.value.private_health_fund || null,
    private_policy_number: form.value.private_policy_number || null,
    invoice_receiver_name: form.value.invoice_receiver_name || null,
    invoice_receiver_phone: form.value.invoice_receiver_phone || null,
    invoice_receiver_email: form.value.invoice_receiver_email || null,
    invoice_receiver_address: form.value.invoice_receiver_address || null
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
