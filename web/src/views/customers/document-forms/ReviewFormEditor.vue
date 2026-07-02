<template>
  <div class="review-form-editor">
    <el-form :model="form" ref="formRef" label-width="180px">
      <el-form-item :label="$t('customerDoc.documentName')">
        <el-input v-model="form.name" :placeholder="$t('customerDoc.documentNamePlaceholder')" />
      </el-form-item>
      <el-divider content-position="left">{{ $t('reviewForm.goals') }}</el-divider>
      <el-table :data="form.goals" border>
        <el-table-column :label="$t('reviewForm.goalName')" min-width="160">
          <template #default="{ row }">
            <el-input v-model="row.name" size="small" :placeholder="$t('reviewForm.goalNamePlaceholder')" />
          </template>
        </el-table-column>
        <el-table-column :label="$t('reviewForm.achieved')" width="120">
          <template #default="{ row }">
            <el-select v-model="row.achieved" size="small" :placeholder="$t('reviewForm.achievedPlaceholder')" clearable style="width: 100%">
              <el-option :label="$t('common.yes')" value="yes" />
              <el-option :label="$t('common.no')" value="no" />
              <el-option :label="$t('reviewForm.partial')" value="partial" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column :label="$t('reviewForm.analysis')" min-width="200">
          <template #default="{ row }">
            <el-input v-model="row.analysis" size="small" type="textarea" :autosize="{ minRows: 1 }" :placeholder="$t('reviewForm.analysisPlaceholder')" />
          </template>
        </el-table-column>
        <el-table-column width="60">
          <template #default="{ $index }">
            <el-button type="danger" size="small" link @click="removeGoalRow($index)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button type="primary" plain size="small" @click="addGoalRow" style="margin-top: 8px">
        {{ $t('reviewForm.addGoal') }}
      </el-button>
      <el-form-item style="margin-top: 16px">
        <el-checkbox v-model="form.syncToRisk">{{ $t('reviewForm.syncToRisk') }}</el-checkbox>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
defineOptions({ name: 'ReviewFormEditor' })
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
  goals: [{ name: '', achieved: '', analysis: '' }],
  syncToRisk: true
})

function addGoalRow() {
  form.value.goals.push({ name: '', achieved: '', analysis: '' })
}

function removeGoalRow(index) {
  if (form.value.goals.length > 1) {
    form.value.goals.splice(index, 1)
  }
}

watch(
  () => props.doc,
  (doc) => {
    if (!doc) return
    form.value.name = doc.name || ''
    if (doc.form_data && typeof doc.form_data === 'object') {
      form.value.syncToRisk = doc.form_data.syncToRisk ?? true
      if (Array.isArray(doc.form_data.goals) && doc.form_data.goals.length > 0) {
        form.value.goals = doc.form_data.goals.map((g) => ({
          name: g.name ?? '',
          achieved: g.achieved ?? '',
          analysis: g.analysis ?? ''
        }))
      }
    }
  },
  { immediate: true }
)

const getFormData = () => ({
  name: form.value.name,
  form_data: {
    goals: form.value.goals,
    syncToRisk: form.value.syncToRisk
  }
})

const validate = async () => getFormData()

defineExpose({ validate, getFormData })
</script>
