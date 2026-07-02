<template>
  <div class="service-agreement-editor">
    <el-form :model="form" ref="formRef" label-width="200px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('serviceAgreement.serviceType')">
        <el-select v-model="form.service_type" :placeholder="$t('serviceAgreement.serviceTypePlaceholder')" style="width: 100%">
          <el-option :label="$t('serviceAgreement.disabilitySupport')" value="disability_support" />
          <el-option :label="$t('serviceAgreement.other')" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('serviceAgreement.cancellationDays')">
        <el-radio-group v-model="form.cancellation_days">
          <el-radio :label="7">{{ $t('serviceAgreement.sevenDays') }}</el-radio>
          <el-radio :label="2">{{ $t('serviceAgreement.twoDays') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item :label="$t('serviceAgreement.withdrawNotice')">
        <el-input v-model="form.withdraw_notice_weeks" type="number" :min="1" :max="52" style="width: 120px" />
        <span class="unit"> {{ $t('serviceAgreement.weeks') }}</span>
      </el-form-item>
      <el-divider content-position="left">{{ $t('serviceAgreement.scheduleOfSupports') }}</el-divider>
      <el-table :data="form.schedule_of_supports" border>
        <el-table-column :label="$t('serviceAgreement.itemCode')" width="160">
          <template #default="{ row }">
            <el-input v-model="row.code" size="small" placeholder="e.g. 04_104_0125_6_1" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('serviceAgreement.unitPrice')" width="120">
          <template #default="{ row }">
            <el-input-number v-model="row.unit_price" size="small" :min="0" :precision="2" controls-position="right" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('serviceAgreement.hours')" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.hours" size="small" :min="0" :precision="2" controls-position="right" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('serviceAgreement.budget')" width="120">
          <template #default="{ row }">
            <el-input-number v-model="row.budget" size="small" :min="0" :precision="2" controls-position="right" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column width="60">
          <template #default="{ $index }">
            <el-button type="danger" size="small" link @click="removeScheduleRow($index)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" plain size="small" @click="addScheduleRow" style="margin-top: 8px">
        {{ $t('serviceAgreement.addItem') }}
      </el-button>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'ServiceAgreementEditor' })
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
  service_type: 'disability_support',
  cancellation_days: 7,
  withdraw_notice_weeks: 4,
  schedule_of_supports: [{ code: '', unit_price: null, hours: null, budget: null }]
})

function addScheduleRow() {
  form.value.schedule_of_supports.push({ code: '', unit_price: null, hours: null, budget: null })
}

function removeScheduleRow(index) {
  if (form.value.schedule_of_supports.length > 1) {
    form.value.schedule_of_supports.splice(index, 1)
  }
}

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.service_type = doc.form_data.service_type ?? 'disability_support'
      form.value.cancellation_days = doc.form_data.cancellation_days ?? 7
      form.value.withdraw_notice_weeks = doc.form_data.withdraw_notice_weeks ?? 4
      if (Array.isArray(doc.form_data.schedule_of_supports) && doc.form_data.schedule_of_supports.length > 0) {
        form.value.schedule_of_supports = doc.form_data.schedule_of_supports.map((r) => ({
          code: r.code ?? '',
          unit_price: r.unit_price ?? null,
          hours: r.hours ?? null,
          budget: r.budget ?? null
        }))
      }
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    service_type: form.value.service_type,
    cancellation_days: form.value.cancellation_days,
    withdraw_notice_weeks: form.value.withdraw_notice_weeks ?? 4,
    schedule_of_supports: form.value.schedule_of_supports
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>

<style scoped>
.unit { margin-left: 8px; }
</style>
