<template>
  <div class="emergency-plan-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('emergencyPlan.fireLogic')">
        <el-input v-model="form.fire_logic" disabled :placeholder="$t('emergencyPlan.fireLogicValue')" />
      </el-form-item>
      <el-form-item :label="$t('emergencyPlan.bombLogic')">
        <el-input v-model="form.bomb_logic" disabled :placeholder="$t('emergencyPlan.bombLogicValue')" />
      </el-form-item>
      <el-form-item :label="$t('emergencyPlan.poisonCenterTel')">
        <el-input v-model="form.poison_center_tel" :placeholder="$t('emergencyPlan.poisonCenterPlaceholder')" />
      </el-form-item>
      <el-form-item :label="$t('emergencyPlan.individualProfile')">
        <el-input v-model="form.individual_profile" type="textarea" :rows="4" :placeholder="$t('emergencyPlan.individualProfilePlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('emergencyPlan.drillRecords') }}</el-divider>
      <el-table :data="form.drill_records" border>
        <el-table-column :label="$t('emergencyPlan.drillDate')" width="180">
          <template #default="{ row }">
            <el-date-picker v-model="row.date" type="date" value-format="YYYY-MM-DD" size="small" style="width: 100%" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('emergencyPlan.drillFeedback')">
          <template #default="{ row }">
            <el-input v-model="row.feedback" size="small" type="textarea" :autosize="{ minRows: 1 }" placeholder="" />
          </template>
        </el-table-column>
        <el-table-column width="60">
          <template #default="{ $index }">
            <el-button type="danger" size="small" link @click="removeDrillRow($index)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" plain size="small" @click="addDrillRow" style="margin-top: 8px">
        {{ $t('emergencyPlan.addDrillRecord') }}
      </el-button>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'EmergencyPlanEditor' })
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  doc: { type: Object, required: true },
  customerId: { type: String, required: true }
})

const formRef = ref(null)
const FIRE_LOGIC = 'Close doors as you go – do not lock them.'
const BOMB_LOGIC = 'Leave doors open.'

const form = ref({
  name: '',
  fire_logic: FIRE_LOGIC,
  bomb_logic: BOMB_LOGIC,
  poison_center_tel: '13 11 26',
  individual_profile: '',
  drill_records: [{ date: '', feedback: '' }]
})

function addDrillRow() {
  form.value.drill_records.push({ date: '', feedback: '' })
}

function removeDrillRow(index) {
  if (form.value.drill_records.length > 1) {
    form.value.drill_records.splice(index, 1)
  }
}

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.fire_logic = doc.form_data.fire_logic ?? FIRE_LOGIC
      form.value.bomb_logic = doc.form_data.bomb_logic ?? BOMB_LOGIC
      form.value.poison_center_tel = doc.form_data.poison_center_tel ?? '13 11 26'
      form.value.individual_profile = doc.form_data.individual_profile ?? ''
      if (Array.isArray(doc.form_data.drill_records) && doc.form_data.drill_records.length > 0) {
        form.value.drill_records = doc.form_data.drill_records.map((r) => ({
          date: r.date ?? '',
          feedback: r.feedback ?? ''
        }))
      }
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    fire_logic: form.value.fire_logic,
    bomb_logic: form.value.bomb_logic,
    poison_center_tel: form.value.poison_center_tel || null,
    individual_profile: form.value.individual_profile || null,
    drill_records: form.value.drill_records
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
