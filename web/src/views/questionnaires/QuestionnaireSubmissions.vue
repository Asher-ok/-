<template>
  <div class="questionnaire-submissions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
        </div>
      </template>

      <div class="filter-bar">
        <el-select
          v-model="filters.questionnaire"
          :placeholder="$t('questionnaireSubmissions.questionnaire')"
          clearable
          filterable
          allow-create
          default-first-option
          :style="{ width: isMobile ? '100%' : '240px' }"
        >
          <el-option v-for="opt in questionnaireOptions" :key="opt" :label="opt" :value="opt" />
        </el-select>
        <el-select
          v-model="filters.employee"
          :placeholder="$t('questionnaireSubmissions.employee')"
          clearable
          filterable
          allow-create
          default-first-option
          :style="{ width: isMobile ? '100%' : '240px' }"
        >
          <el-option v-for="opt in employeeOptions" :key="opt" :label="opt" :value="opt" />
        </el-select>
        <el-select
          v-model="filters.customer"
          :placeholder="$t('questionnaireSubmissions.customer')"
          clearable
          filterable
          allow-create
          default-first-option
          :style="{ width: isMobile ? '100%' : '240px' }"
        >
          <el-option v-for="opt in customerOptions" :key="opt" :label="opt" :value="opt" />
        </el-select>
        <el-button type="primary" @click="handleSearch">{{ $t('common.search') }}</el-button>
        <el-button @click="handleReset">{{ $t('task.reset') }}</el-button>
      </div>

      <el-table
        :data="pagedResponses"
        v-loading="loading"
        stripe
        table-layout="auto"
        style="width: 100%"
        :default-sort="{ prop: 'submitted_at', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="questionnaire_title" :label="$t('questionnaireSubmissions.questionnaire')">
          <template #default="{ row }">
            <el-link type="primary" class="clickable-text" :underline="true" @click="handleView(row)">{{ row.questionnaire_title || '-' }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="customer_name" :label="$t('questionnaireSubmissions.customer')" min-width="140" />
        <el-table-column prop="employee_name" :label="$t('questionnaireSubmissions.employee')" min-width="120" />
        <el-table-column prop="task_title" :label="$t('questionnaireSubmissions.task')" min-width="160" show-overflow-tooltip />
        <el-table-column prop="submitted_at" column-key="submitted_at" :label="$t('questionnaireSubmissions.submittedAt')" min-width="240" sortable="custom">
          <template #default="{ row }">
            <span>{{ formatDateTimeToMinute(row.submitted_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('questionnaireSubmissions.operations')" width="140" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleDelete(row)">{{ $t('questionnaireSubmissions.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-bar">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10]"
          layout="total, prev, pager, next"
          :total="total"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" :title="$t('questionnaireSubmissions.submissionDetail')" width="600px">
      <div v-if="detail" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('questionnaireSubmissions.questionnaire')">{{ detail.questionnaire_title }}</el-descriptions-item>
          <el-descriptions-item :label="$t('questionnaireSubmissions.customer')">{{ detail.customer_name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('questionnaireSubmissions.employee')">{{ detail.employee_name }}</el-descriptions-item>
          <el-descriptions-item :label="$t('questionnaireSubmissions.task')">{{ detail.task_title }}</el-descriptions-item>
          <el-descriptions-item :label="$t('questionnaireSubmissions.submittedAt')" :span="2">{{ formatDateTimeToMinute(detail.submitted_at) }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <div class="answers-label">{{ $t('questionnaireSubmissions.answers') }}</div>
        <QuestionAnswerDisplay :detail="detail" />
      </div>
      <template #footer>
        <el-button type="primary" :disabled="!detail" @click="handleExport">{{ $t('questionnaireSubmissions.exportPDF') }}</el-button>
        <el-button @click="detailVisible = false">{{ $t('questionnaireSubmissions.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, inject, reactive, watch } from 'vue'
import { getQuestionnaireResponses, getQuestionnaireResponse, exportQuestionnaireResponse, deleteQuestionnaireResponse } from '@/api/questionnaires'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import QuestionAnswerDisplay from '@/components/QuestionAnswerDisplay.vue'
import { formatDateTimeToMinute } from '@/utils/formatters'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))

const pageTitle = computed(() => {
  const base = t('menu.questionnaires')
  const sub = t('questionnaire.submissions')
  return `${base}/${sub}`
})

const responses = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const detail = ref(null)
const sortState = reactive({
  prop: 'submitted_at',
  order: 'descending'
})
const filters = reactive({
  questionnaire: '',
  employee: '',
  customer: ''
})
const page = ref(1)
const pageSize = ref(10)

const loadResponses = async () => {
  loading.value = true
  try {
    responses.value = await getQuestionnaireResponses()
  } catch (error) {
    ElMessage.error(t('questionnaireSubmissions.loadFailed'))
  } finally {
    loading.value = false
  }
}

const normalizeString = (v) => (v == null ? '' : String(v)).trim()
const includesText = (source, keyword) => {
  const s = normalizeString(source).toLowerCase()
  const k = normalizeString(keyword).toLowerCase()
  if (!k) return true
  return s.includes(k)
}

const uniqueNonEmpty = (arr) => {
  const set = new Set()
  for (const v of arr) {
    const s = normalizeString(v)
    if (s) set.add(s)
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b))
}

const questionnaireOptions = computed(() => uniqueNonEmpty((responses.value || []).map((r) => r?.questionnaire_title)))
const employeeOptions = computed(() => uniqueNonEmpty((responses.value || []).map((r) => r?.employee_name)))
const customerOptions = computed(() => uniqueNonEmpty((responses.value || []).map((r) => r?.customer_name)))

const filteredResponses = computed(() => {
  const list = Array.isArray(responses.value) ? responses.value : []
  const q = normalizeString(filters.questionnaire)
  const e = normalizeString(filters.employee)
  const c = normalizeString(filters.customer)
  if (!q && !e && !c) return list
  return list.filter((r) => {
    if (q && !includesText(r?.questionnaire_title, q)) return false
    if (e && !includesText(r?.employee_name, e)) return false
    if (c && !includesText(r?.customer_name, c)) return false
    return true
  })
})

const toTime = (value) => {
  const time = new Date(value || '').getTime()
  return Number.isFinite(time) ? time : 0
}

const sortedResponses = computed(() => {
  const list = [...filteredResponses.value]
  const { prop, order } = sortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'submitted_at') {
    return list.sort((a, b) => (toTime(a?.submitted_at) - toTime(b?.submitted_at)) * dir)
  }
  return list
})

const total = computed(() => sortedResponses.value.length)
const pagedResponses = computed(() => {
  const list = sortedResponses.value
  const p = Number(page.value) || 1
  const size = Number(pageSize.value) || 10
  const start = (p - 1) * size
  return list.slice(start, start + size)
})

const handleSortChange = ({ prop, order }) => {
  sortState.prop = prop || ''
  sortState.order = order
  page.value = 1
}

const handleSearch = () => {
  page.value = 1
}

const handleReset = () => {
  filters.questionnaire = ''
  filters.employee = ''
  filters.customer = ''
  page.value = 1
}

const handleView = async (row) => {
  try {
    detail.value = await getQuestionnaireResponse(row.id)
    detailVisible.value = true
  } catch (error) {
    ElMessage.error(t('questionnaireSubmissions.loadDetailFailed'))
  }
}

const handleExport = async () => {
  if (!detail.value?.id) return
  try {
    const blob = await exportQuestionnaireResponse(detail.value.id)
    const fileName = `questionnaire_response_${detail.value.id}.pdf`
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error(t('questionnaireSubmissions.exportFailed'))
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('questionnaireSubmissions.deleteConfirm'), t('questionnaireSubmissions.tip'), { type: 'warning' })
    await deleteQuestionnaireResponse(row.id)
    ElMessage.success(t('questionnaireSubmissions.deleteSuccess'))
    loadResponses()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(t('questionnaireSubmissions.deleteFailed'))
    }
  }
}

onMounted(() => {
  loadResponses()
})

watch(
  () => [filters.questionnaire, filters.employee, filters.customer],
  () => {
    page.value = 1
  }
)
</script>

<style scoped>
.questionnaire-submissions {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.pager-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.detail-content {
  line-height: 1.8;
}

.answers-label {
  font-weight: 600;
  margin-bottom: 8px;
}
</style>
