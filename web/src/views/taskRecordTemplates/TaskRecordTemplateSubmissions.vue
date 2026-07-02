<template>
  <div class="template-submissions">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
        </div>
      </template>

      <el-table
        :data="rows"
        v-loading="loading"
        stripe
        table-layout="auto"
        style="width: 100%"
        :default-sort="{ prop: 'submitted_at', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="template_title" :label="$t('taskRecordTemplateSubmissions.template')" min-width="160" />
        <el-table-column prop="customer_name" :label="$t('taskRecordTemplateSubmissions.customer')" min-width="140" />
        <el-table-column prop="employee_name" :label="$t('taskRecordTemplateSubmissions.employee')" min-width="120" />
        <el-table-column prop="task_title" :label="$t('taskRecordTemplateSubmissions.task')" min-width="160" show-overflow-tooltip />
        <el-table-column
          prop="submitted_at"
          column-key="submitted_at"
          :label="$t('taskRecordTemplateSubmissions.submittedAt')"
          min-width="220"
          sortable="custom"
        >
          <template #default="{ row }">
            <span>{{ formatDateTimeToMinute(row.submitted_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('taskRecordTemplateSubmissions.operations')" width="180" :fixed="isMobile ? false : 'right'" align="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="handleView(row)">{{ $t('taskRecordTemplateSubmissions.view') }}</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">{{ $t('taskRecordTemplateSubmissions.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-bar">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @current-change="load"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="detailVisible" :title="$t('taskRecordTemplateSubmissions.detailTitle')" width="720px">
      <div v-if="detail" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('taskRecordTemplateSubmissions.template')">{{ detail.template_title || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskRecordTemplateSubmissions.questionnaire')">{{ detail.questionnaire_title || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskRecordTemplateSubmissions.customer')">{{ detail.customer_name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskRecordTemplateSubmissions.employee')">{{ detail.employee_name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskRecordTemplateSubmissions.task')" :span="2">{{ detail.task_title || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('taskRecordTemplateSubmissions.submittedAt')" :span="2">
            {{ formatDateTimeToMinute(detail.submitted_at) }}
          </el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <div class="json-title">{{ $t('taskRecordTemplateSubmissions.data') }}</div>
        <pre class="json-box">{{ prettyJson(detail.record_data) }}</pre>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">{{ $t('taskRecordTemplateSubmissions.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'TaskRecordTemplateSubmissions' })
import { ref, computed, inject, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTimeToMinute } from '@/utils/formatters'
import { getTaskRecordSubmissions, getTaskRecordSubmission, deleteTaskRecordSubmission } from '@/api/taskRecords'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))

const pageTitle = computed(() => `${t('menu.taskRecordTemplates')}/${t('taskRecordTemplate.submissions')}`)

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const sortState = reactive({ prop: 'submitted_at', order: 'descending' })

const detailVisible = ref(false)
const detail = ref(null)

const normalizeOrder = (order) => (order === 'ascending' ? 'asc' : 'desc')

const load = async () => {
  loading.value = true
  try {
    const res = await getTaskRecordSubmissions({
      page: page.value,
      page_size: pageSize.value,
      sort: normalizeOrder(sortState.order)
    })
    rows.value = Array.isArray(res?.items) ? res.items : []
    total.value = Number(res?.total || 0)
  } catch (e) {
    ElMessage.error(t('taskRecordTemplateSubmissions.loadFailed'))
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (size) => {
  pageSize.value = Number(size) || 10
  page.value = 1
  load()
}

const handleSortChange = ({ prop, order }) => {
  if (prop !== 'submitted_at') return
  sortState.prop = prop || 'submitted_at'
  sortState.order = order || 'descending'
  page.value = 1
  load()
}

const handleView = async (row) => {
  try {
    detail.value = await getTaskRecordSubmission(row.id)
    detailVisible.value = true
  } catch (e) {
    ElMessage.error(t('taskRecordTemplateSubmissions.loadDetailFailed'))
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('taskRecordTemplateSubmissions.deleteConfirm'), t('taskRecordTemplateSubmissions.tip'), { type: 'warning' })
    await deleteTaskRecordSubmission(row.id)
    ElMessage.success(t('taskRecordTemplateSubmissions.deleteSuccess'))
    load()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(t('taskRecordTemplateSubmissions.deleteFailed'))
    }
  }
}

const prettyJson = (value) => {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return String(value ?? '')
  }
}

load()
</script>

<style scoped>
.template-submissions {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pager-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.json-title {
  font-weight: 700;
  margin-bottom: 10px;
}

.json-box {
  max-height: 360px;
  overflow: auto;
  background: #0b1020;
  color: #e5e7eb;
  padding: 12px;
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
