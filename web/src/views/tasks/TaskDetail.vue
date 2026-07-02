<template>
  <div class="task-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ $t('taskDetail.title') }}</span>
          <div class="header-actions">
            <el-button v-if="showRejectAction" type="warning" @click="handleRejectAction">
              {{ rejectActionLabel }}
            </el-button>
            <el-button v-if="showApproveAction" type="success" @click="handleApproveAction">{{ $t('task.approve') }}</el-button>
            <el-button v-if="showCancelAction" type="info" @click="handleCancelAction">{{ $t('task.cancel') }}</el-button>
            <el-button @click="handleBack">{{ $t('taskDetail.return') }}</el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="$t('taskDetail.titleLabel')">{{ task.title }}</el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.status')">
          <el-tag :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.customer')">{{ task.customer?.name }}</el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.serviceStartTime')">
          {{ serviceStartText }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.serviceEndTime')">
          {{ serviceEndText }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.description')" :span="2">{{ task.description }}</el-descriptions-item>
        <el-descriptions-item :label="$t('task.assignedEmployeeLabel')" :span="2">{{ assignedEmployeeText }}</el-descriptions-item>
        <el-descriptions-item :label="$t('taskDetail.employeeRemark')" :span="2">{{ employeeRemarkText }}</el-descriptions-item>
      </el-descriptions>
      
      <el-divider />
      
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="$t('task.services')" name="services" lazy>
          <el-table v-if="taskServiceRows.length" :data="taskServiceRows" stripe>
            <el-table-column prop="service_code" :label="$t('task.serviceCode')" min-width="160" />
            <el-table-column prop="unit_price" :label="$t('task.unitPrice')" width="120">
              <template #default="{ row }">
                <span>{{ formatCurrency(row.unit_price) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="duration_hours" :label="$t('task.serviceDurationHours')" width="140">
              <template #default="{ row }">
                <span>{{ row.duration_hours ?? '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="total_price" :label="$t('task.totalPrice')" width="140">
              <template #default="{ row }">
                <span>{{ formatCurrency(row.total_price) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="service_time_start" :label="$t('task.serviceStartTime')" min-width="170" />
            <el-table-column prop="service_time_end" :label="$t('task.serviceEndTime')" min-width="170" />
            <el-table-column prop="latest_claim_time" :label="$t('task.latestClaimTime')" min-width="170" />
          </el-table>
          <el-empty v-else :description="$t('task.noServices')" />
        </el-tab-pane>
        <el-tab-pane :label="$t('taskDetail.questionnaireData')" name="questionnaire" lazy>
          <div v-if="questionnaireLoading" class="loading-text">{{ $t('taskDetail.loading') }}</div>
          <template v-else>
            <div v-if="questionnaireResponses.length > 0" class="questionnaire-responses">
              <div v-if="questionnaireResponses.length > 1" class="response-selector" style="margin-bottom: 20px">
                <el-radio-group v-model="selectedResponseId">
                  <el-radio-button v-for="r in questionnaireResponses" :key="r.id" :label="r.id">
                    {{ r.title || $t('task.questionnaire') }}
                  </el-radio-button>
                </el-radio-group>
              </div>
              <QuestionAnswerDisplay v-if="questionnaireDetail" :detail="questionnaireDetail" />
            </div>
            <el-empty v-else :description="$t('taskDetail.noQuestionnaireData')" />
          </template>
        </el-tab-pane>
        <el-tab-pane :label="$t('taskDetail.signature')" name="signature" lazy>
          <div class="tab-toolbar">
            <el-button type="primary" @click="openSignatureDialog">
              {{ signatureSrc ? $t('common.edit') : $t('common.add') }}
            </el-button>
            <el-button v-if="signatureSrc" type="danger" @click="handleDeleteSignature">{{ $t('common.delete') }}</el-button>
          </div>
          <img v-if="signatureSrc" :src="signatureSrc" style="max-width: 100%" />
          <el-empty v-else :description="$t('taskDetail.noSignature')" />
        </el-tab-pane>
        <el-tab-pane :label="$t('taskDetail.photos')" name="photos" lazy>
          <div class="tab-toolbar">
            <el-upload
              :show-file-list="false"
              :auto-upload="false"
              accept="image/*"
              multiple
              @change="handlePhotoUploadChange"
            >
              <el-button type="primary">{{ $t('common.add') }}</el-button>
            </el-upload>
          </div>
          <el-row :gutter="20">
            <el-col v-for="(photo, index) in photoItems" :key="photo.id || index" :span="6">
              <div class="photo-card">
                <el-image
                  :src="photo.src"
                  :preview-src-list="photoPreviewSrcs"
                  :initial-index="index"
                  :preview-teleported="false"
                  style="width: 100%; height: 220px; background: #f5f7fa"
                  fit="contain"
                />
                <div class="photo-actions">
                  <el-upload
                    :show-file-list="false"
                    :auto-upload="false"
                    accept="image/*"
                    @change="(file) => handleReplacePhoto(photo, file)"
                  >
                    <el-button size="small">{{ $t('common.edit') }}</el-button>
                  </el-upload>
                  <el-button size="small" type="danger" :disabled="!photo.id" @click="handleDeletePhoto(photo)">
                    {{ $t('common.delete') }}
                  </el-button>
                </div>
              </div>
            </el-col>
          </el-row>
          <el-empty v-if="photoItems.length === 0" :description="$t('taskDetail.noPhotos')" />
        </el-tab-pane>
        <el-tab-pane :label="$t('incidentReport.tabTitle')" name="incident" lazy>
          <div class="tab-toolbar">
            <el-button type="primary" @click="openIncidentDialog()">{{ $t('common.add') }}</el-button>
          </div>
          <div v-if="incidentReports.length > 0" class="incident-list">
            <el-descriptions v-for="r in incidentReports" :key="r.id" :column="1" border class="incident-item">
              <el-descriptions-item :label="$t('incidentReport.incidentType')">{{ r.incident_type || '-' }}</el-descriptions-item>
              <el-descriptions-item :label="$t('incidentReport.description')">{{ r.description || '-' }}</el-descriptions-item>
              <el-descriptions-item :label="$t('incidentReport.occurredAt')">{{ r.occurred_at ? formatDateTime(r.occurred_at) : '-' }}</el-descriptions-item>
              <el-descriptions-item
                v-for="row in getIncidentReportRows(r)"
                :key="`${r.id}-${row.key}`"
                :label="row.label"
              >
                {{ row.value }}
              </el-descriptions-item>
              <el-descriptions-item :label="$t('common.actions')">
                <div class="inline-actions">
                  <el-button size="small" @click="openIncidentDialog(r)">{{ $t('common.edit') }}</el-button>
                  <el-button size="small" type="danger" @click="handleDeleteIncident(r)">{{ $t('common.delete') }}</el-button>
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else :description="$t('incidentReport.none')" />
        </el-tab-pane>
        <el-tab-pane :label="$t('taskDetail.taskRecord')" name="taskRecord" lazy>
          <div v-if="taskRecordLoading" class="loading-text">{{ $t('taskDetail.loading') }}</div>
          <template v-else>
            <div v-if="taskRecordTemplate" class="task-record-meta">
              <el-descriptions :column="1" border>
                <el-descriptions-item :label="$t('taskDetail.template')">
                  {{ resolveLocalizedText(taskRecordTemplate.title_i18n, taskRecordTemplate.title) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
            <div v-if="taskRecordRows.length" class="task-record-content">
              <el-descriptions :column="1" border>
                <el-descriptions-item v-for="row in taskRecordRows" :key="row.key" :label="row.label">
                  <template v-if="(row.type === 'multiple_choice' || row.type === 'checkbox') && row.options.length">
                    <div class="task-record-checkboxes">
                      <el-checkbox-group :model-value="row.selected" disabled>
                        <el-checkbox v-for="opt in row.options" :key="opt.id" :label="opt.id">
                          {{ opt.label }}
                        </el-checkbox>
                      </el-checkbox-group>
                    </div>
                  </template>
                  <template v-else>
                    {{ row.value }}
                  </template>
                </el-descriptions-item>
              </el-descriptions>
            </div>
            <el-empty v-else :description="$t('taskDetail.noTaskRecord')" />
          </template>
        </el-tab-pane>
        <el-tab-pane :label="$t('taskDetail.tracking')" name="tracking" lazy>
          <div v-if="trackingLoading" class="loading-text">{{ $t('taskDetail.loading') }}</div>
          <template v-else>
            <div v-if="trackingRecords.length > 0" class="tracking-section">
              <el-descriptions :column="4" border>
                <el-descriptions-item :label="$t('taskDetail.recordCount')">
                  {{ trackingRecords.length }}
                </el-descriptions-item>
                <el-descriptions-item :label="$t('taskDetail.startTime')">
                  {{ trackingStats.startTime }}
                </el-descriptions-item>
                <el-descriptions-item :label="$t('taskDetail.endTime')">
                  {{ trackingStats.endTime }}
                </el-descriptions-item>
                <el-descriptions-item :label="$t('taskDetail.totalDuration')">
                  {{ trackingStats.durationText }}
                </el-descriptions-item>
              </el-descriptions>
              <div ref="trackingMapRef" class="tracking-map" />
              <el-table :data="trackingRecords" stripe>
                <el-table-column
                  prop="recorded_at"
                  :label="$t('taskDetail.time')"
                  min-width="180"
                >
                  <template #default="{ row }">
                    {{ formatDateTime(row.recorded_at) }}
                  </template>
                </el-table-column>
                <el-table-column
                  prop="latitude"
                  :label="$t('taskDetail.latitude')"
                  min-width="120"
                />
                <el-table-column
                  prop="longitude"
                  :label="$t('taskDetail.longitude')"
                  min-width="120"
                />
                <el-table-column
                  prop="address"
                  :label="$t('taskDetail.address')"
                  min-width="200"
                  show-overflow-tooltip
                />
              </el-table>
            </div>
            <el-empty v-else :description="$t('taskDetail.noTrackingRecords')" />
          </template>
        </el-tab-pane>
        
      </el-tabs>
    </el-card>

    <el-dialog v-model="signatureDialogVisible" :title="signatureSrc ? $t('common.edit') : $t('common.add')" width="720px">
      <div class="signature-dialog">
        <canvas
          ref="signatureCanvasRef"
          class="signature-canvas"
          @mousedown="startSignature"
          @mousemove="moveSignature"
          @mouseup="endSignature"
          @mouseleave="endSignature"
          @touchstart.prevent="startSignature"
          @touchmove.prevent="moveSignature"
          @touchend.prevent="endSignature"
        />
        <div class="inline-actions">
          <el-button @click="clearSignatureCanvas">{{ $t('common.clear') }}</el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="signatureDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveSignature">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="incidentDialogVisible" :title="incidentForm.id ? $t('common.edit') : $t('common.add')" width="640px">
      <el-form label-width="100px">
        <el-form-item :label="$t('incidentReport.incidentType')">
          <el-input v-model="incidentForm.incident_type" clearable />
        </el-form-item>
        <el-form-item :label="$t('incidentReport.description')">
          <el-input v-model="incidentForm.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item :label="$t('incidentReport.occurredAt')">
          <el-date-picker
            v-model="incidentForm.occurred_at"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="incidentDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveIncident">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getTask,
  getTaskLocationTracks,
  approveTask,
  rejectTask,
  cancelTask,
  updateTaskSignature,
  deleteTaskSignature,
  uploadTaskPhotos,
  deleteTaskPhoto
} from '@/api/tasks'
import { getQuestionnaires, getQuestionnaireResponses, getQuestionnaireResponse } from '@/api/questionnaires'
import { getIncidentReports, createIncidentReport, updateIncidentReport, deleteIncidentReport } from '@/api/incidentReports'
import { getTaskRecord } from '@/api/taskRecords'
import { getIncidentTemplates } from '@/api/incidentTemplates'
import api from '@/api/index'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import QuestionAnswerDisplay from '@/components/QuestionAnswerDisplay.vue'
import { formatDateTimeToMinute } from '@/utils/formatters'
import { markUpdatesRead } from '@/api/updates'

const { t, locale: i18n } = useI18n()

const route = useRoute()
const router = useRouter()
const taskId = route.params.id
let isDisposed = false
const task = ref({})
const loading = ref(false)
const activeTab = ref('services')
const signatureSrc = ref('')
const photoItems = ref([])
const questionnaireResponses = ref([])
const questionnaireLoading = ref(false)
const selectedResponseId = ref(null)
const questionnaireDetail = computed(() => {
  if (!selectedResponseId.value) return null
  return questionnaireResponses.value.find(r => r.id === selectedResponseId.value)
})
const trackingLoading = ref(false)
const trackingRecords = ref([])
const trackingLoaded = ref(false)
const trackingMapRef = ref(null)
const incidentReports = ref([])
const incidentTemplates = ref([])
const taskRecordLoading = ref(false)
const taskRecordTemplate = ref(null)
const taskRecord = ref(null)
const signatureDialogVisible = ref(false)
const signatureCanvasRef = ref(null)
const signatureDrawing = ref(false)
const signatureHasStroke = ref(false)
const incidentDialogVisible = ref(false)
const incidentForm = reactive({
  id: '',
  incident_type: '',
  description: '',
  occurred_at: ''
})
let trackingMap = null
let trackingLine = null

const normalizeString = (v) => (v == null ? '' : String(v)).trim()
const resolveLocalizedText = (i18nValue, fallback = '') => {
  const lang = String(i18n.value || 'zh').toLowerCase().startsWith('en') ? 'en' : 'zh'
  if (i18nValue && typeof i18nValue === 'object') {
    const direct = normalizeString(i18nValue[lang])
    const alternate = normalizeString(i18nValue[lang === 'zh' ? 'en' : 'zh'])
    if (direct) return direct
    if (alternate) return alternate
  }
  return normalizeString(fallback)
}

const taskRecordRows = computed(() => {
  const template = taskRecordTemplate.value
  const record = taskRecord.value
  const answers = record?.record_data && typeof record.record_data === 'object' ? record.record_data : {}
  const questions = template?.schema_json?.questions
  if (!Array.isArray(questions) || !questions.length) return []
  return questions.map((q) => {
    const key = q?.id || q?.key || q?.name || ''
    const label = resolveLocalizedText(q?.title_i18n, q?.title || key)
    const raw = key ? answers[key] : null
    const type = (q?.type || '').toString()
    const optionsRaw = Array.isArray(q?.options) ? q.options : []
    const options = optionsRaw.map((opt) => {
      const id = (opt?.id || opt?.value || opt?.key || '').toString()
      const fallback = (opt?.text || opt?.label || opt?.title || id).toString()
      const optLabel = resolveLocalizedText(opt?.text_i18n, fallback)
      return { id: id || optLabel, label: optLabel || id }
    })

    if (type === 'single_choice' && options.length) {
      const selectedId = raw == null ? '' : String(raw)
      const matched = options.find((o) => String(o.id) === selectedId)
      return { key: key || label, label, type, value: matched?.label || selectedId || '-' , options: [], selected: [] }
    }

    if ((type === 'multiple_choice' || type === 'checkbox') && options.length) {
      const selected =
        Array.isArray(raw)
          ? raw.map((v) => String(v))
          : (raw == null ? [] : [String(raw)])
      return { key: key || label, label, type, value: '-', options, selected }
    }

    const value = Array.isArray(raw) ? raw.join(', ') : (raw == null ? '' : String(raw))
    return { key: key || label, label, type, value: value || '-', options: [], selected: [] }
  })
})

const getIncidentReportRows = (report) => {
  const templateId = report?.template_id || task.value?.incident_template_id || null
  const templates = Array.isArray(incidentTemplates.value) ? incidentTemplates.value : []
  const template =
    (templateId ? templates.find((t) => String(t.id) === String(templateId)) : null) || templates[0] || null
  const questions = template?.schema_json?.questions
  const rawData = report?.report_data && typeof report.report_data === 'object' ? report.report_data : {}
  if (!Array.isArray(questions) || !questions.length) {
    const keys = Object.keys(rawData || {})
    if (!keys.length) return []
    return keys.slice(0, 30).map((k) => ({ key: k, label: k, value: Array.isArray(rawData[k]) ? rawData[k].join(', ') : String(rawData[k]) }))
  }
  return questions.map((q) => {
    const key = q?.id || q?.key || q?.name || ''
    const label = resolveLocalizedText(q?.title_i18n, q?.title || key)
    const raw = key ? rawData[key] : null
    const value = Array.isArray(raw) ? raw.join(', ') : (raw == null ? '' : String(raw))
    return { key: key || label, label, value: value || '-' }
  })
}
let trackingMarkers = null

const serviceStartText = computed(() => {
  const value = task.value?.service_start_time || task.value?.service_time
  if (value) return formatDateTimeToMinute(value)
  const list = Array.isArray(task.value?.services) ? task.value.services : []
  const times = list.map((s) => s?.service_time_start || s?.service_start_time).filter(Boolean).sort()
  return times.length ? formatDateTimeToMinute(times[0]) : '-'
})

const serviceEndText = computed(() => {
  const value = task.value?.service_end_time
  if (value) return formatDateTimeToMinute(value)
  const list = Array.isArray(task.value?.services) ? task.value.services : []
  const times = list.map((s) => s?.service_time_end || s?.service_end_time).filter(Boolean).sort()
  return times.length ? formatDateTimeToMinute(times[times.length - 1]) : '-'
})

const employeeRemarkText = computed(() => {
  const value =
    task.value?.employee_remark ??
    task.value?.employeeRemark ??
    task.value?.remark ??
    task.value?.employee_note ??
    task.value?.employeeNote ??
    ''
  const text = (value ?? '').toString().trim()
  return text ? text : '-'
})

const assignedEmployeeText = computed(() => {
  const direct = (task.value?.assigned_employee_name || task.value?.assigned_employee?.name || '').toString().trim()
  if (direct) return direct
  return task.value?.assigned_employee_id ? task.value.assigned_employee_id : '-'
})

const photoPreviewSrcs = computed(() => photoItems.value.map((item) => item.src).filter(Boolean))

const formatCurrency = (val) => {
  const n = Number(val)
  if (val == null || val === '' || isNaN(n)) return '-'
  return `$${n.toFixed(2)}`
}

const taskServiceRows = computed(() => {
  const list = Array.isArray(task.value?.services)
    ? task.value.services
    : (Array.isArray(task.value?.service_items) ? task.value.service_items : [])
  return list.map((s) => {
    const unit =
      s?.unit_price_override != null
        ? Number(s.unit_price_override)
        : (s?.unit_price != null ? Number(s.unit_price) : null)
    const hours =
      s?.duration_hours != null
        ? Number(s.duration_hours)
        : (s?.service_duration_hours != null
            ? Number(s.service_duration_hours)
            : (s?.duration != null
                ? Number(s.duration)
                : (s?.hours != null ? Number(s.hours) : (s?.quantity != null ? Number(s.quantity) : null))))
    const totalDirect =
      s?.total_price != null
        ? Number(s.total_price)
        : (s?.amount != null
            ? Number(s.amount)
            : (s?.total_amount != null
                ? Number(s.total_amount)
                : (s?.line_total != null ? Number(s.line_total) : (s?.total != null ? Number(s.total) : null))))
    const totalDerived = unit != null && hours != null ? Number((unit * hours).toFixed(2)) : null
    return {
      service_code: s?.service_code || s?.code || '-',
      unit_price: unit,
      duration_hours: hours != null && !isNaN(hours) ? hours : null,
      total_price: totalDirect != null && !isNaN(totalDirect) ? totalDirect : totalDerived,
      service_time_start: formatDateTimeToMinute(s?.service_time_start || s?.service_start_time || ''),
      service_time_end: formatDateTimeToMinute(s?.service_time_end || s?.service_end_time || ''),
      latest_claim_time: formatDateTimeToMinute(s?.latest_claim_time || '')
    }
  })
})

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    rejected: 'danger',
    approved: 'success',
    cancelled: 'danger'
  }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = {
    pending: t('task.pending'),
    in_progress: t('task.inProgress'),
    completed: t('task.completed'),
    rejected: t('task.rejected'),
    approved: t('task.approved'),
    cancelled: t('task.cancelled')
  }
  return map[status] || status
}

const handleBack = () => {
  // 强制返回到任务列表页面，避免路由问题
  router.push('/tasks')
}

const showApproveAction = computed(() => task.value?.status === 'completed')
const showRejectAction = computed(() => ['completed', 'rejected', 'approved'].includes(task.value?.status))
const showCancelAction = computed(() => ['pending', 'in_progress'].includes(task.value?.status))

const rejectActionLabel = computed(() => {
  const s = task.value?.status
  if (s === 'rejected' || s === 'approved') return t('task.updateRejectReason')
  return t('task.auditFailed')
})

const handleApproveAction = async () => {
  try {
    await approveTask(taskId)
    ElMessage.success(t('task.approveSuccess'))
    await loadTask()
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || t('task.approveFailed'))
  }
}

const handleRejectAction = async () => {
  try {
    const { value } = await ElMessageBox.prompt(t('task.rejectPrompt'), t('task.rejectTitle'), {
      inputType: 'textarea'
    })
    await rejectTask(taskId, value)
    ElMessage.success(t('task.rejectSuccess'))
    await loadTask()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error?.response?.data?.detail || t('task.rejectFailed'))
    }
  }
}

const handleCancelAction = async () => {
  try {
    const { value } = await ElMessageBox.prompt(t('task.cancelPrompt'), t('task.cancelTitle'), {
      inputType: 'textarea'
    })
    await cancelTask(taskId, value)
    ElMessage.success(t('task.cancelSuccess'))
    await loadTask()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error?.response?.data?.detail || t('task.cancelFailed'))
    }
  }
}

const loadTask = async () => {
  loading.value = true
  try {
    task.value = await getTask(taskId)
    // 并行加载非关键数据，避免一个失败影响其他
    await Promise.allSettled([
      loadSignature(),
      loadPhotos(),
      loadQuestionnaireDetail(),
      loadIncidentReports(),
      loadIncidentTemplates(),
      loadTaskRecord()
    ])
  } catch (error) {
    const errorMessage = error?.response?.data?.detail || error?.message || t('taskDetail.loadTaskFailed')
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

const loadIncidentTemplates = async () => {
  try {
    const res = await getIncidentTemplates()
    incidentTemplates.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } catch {
    incidentTemplates.value = []
  }
}

const loadTaskRecord = async () => {
  taskRecordLoading.value = true
  try {
    const res = await getTaskRecord({ task_id: taskId })
    taskRecordTemplate.value = res?.template || null
    taskRecord.value = res?.record || null
  } catch {
    taskRecordTemplate.value = null
    taskRecord.value = null
  } finally {
    taskRecordLoading.value = false
  }
}

const loadIncidentReports = async () => {
  try {
    incidentReports.value = await getIncidentReports({ task_id: taskId }) || []
  } catch {
    incidentReports.value = []
  }
}

const loadQuestionnaireDetail = async () => {
  questionnaireLoading.value = true
  try {
    const responses = await getQuestionnaireResponses()
    const matched = (responses || [])
      .filter((item) => item.task_id === taskId)
      .sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at))
    
    if (matched.length > 0) {
      const detailedResponses = await Promise.all(
        matched.map(r => getQuestionnaireResponse(r.id))
      )
      questionnaireResponses.value = detailedResponses
      selectedResponseId.value = detailedResponses[0].id
      return
    }

    if (task.value?.questionnaire_data) {
      const templates = await getQuestionnaires()
      const activeTemplate =
        (templates || []).find((item) => item.is_active) || (templates || [])[0]
      if (activeTemplate) {
        const legacyResponse = {
          id: 'legacy',
          title: activeTemplate.title,
          questions: activeTemplate.questions || [],
          answers: task.value.questionnaire_data
        }
        questionnaireResponses.value = [legacyResponse]
        selectedResponseId.value = 'legacy'
      }
    }
  } catch (error) {
    ElMessage.error(t('taskDetail.loadQuestionnaireFailed'))
  } finally {
    questionnaireLoading.value = false
  }
}

const loadSignature = async () => {
  const value = task.value?.signature_image_url
  if (!value) {
    signatureSrc.value = ''
    return
  }
  if (value.startsWith('data:image')) {
    signatureSrc.value = value
    return
  }
  if (value.startsWith('http')) {
    signatureSrc.value = value
    return
  }
  try {
    const blob = await api.get(`/houtai/tasks/${taskId}/signature/image`, {
      responseType: 'blob'
    })
    const dataUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
    signatureSrc.value = dataUrl
  } catch (error) {
    signatureSrc.value = ''
  }
}

const loadPhotos = async () => {
  const urls = Array.isArray(task.value?.photo_urls) ? task.value.photo_urls : []
  if (urls.length === 0) {
    photoItems.value = []
    return
  }

  const results = []
  for (const url of urls) {
    if (!url) continue
    if (url.startsWith('data:image')) {
      results.push({ id: null, src: url, rawUrl: url })
      continue
    }
    const photoId = url.split('/').filter(Boolean).pop()
    if (!photoId) continue
    try {
      const blob = await api.get(`/houtai/tasks/${taskId}/photos/${photoId}`, {
        responseType: 'blob'
      })
      const dataUrl = await new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
      results.push({ id: photoId, src: dataUrl, rawUrl: url })
    } catch (error) {
      // 忽略单张失败
    }
  }
  photoItems.value = results
}

const getCanvasPoint = (event) => {
  const canvas = signatureCanvasRef.value
  if (!canvas) return { x: 0, y: 0 }
  const rect = canvas.getBoundingClientRect()
  const source = event?.touches?.[0] || event
  return {
    x: (source.clientX - rect.left) * (canvas.width / rect.width),
    y: (source.clientY - rect.top) * (canvas.height / rect.height)
  }
}

const initSignatureCanvas = async () => {
  await nextTick()
  const canvas = signatureCanvasRef.value
  if (!canvas) return
  const width = 640
  const height = 320
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, width, height)
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#222222'
  signatureHasStroke.value = false

  if (signatureSrc.value) {
    const img = new Image()
    img.onload = () => {
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, width, height)
      ctx.drawImage(img, 0, 0, width, height)
      signatureHasStroke.value = true
    }
    img.src = signatureSrc.value
  }
}

const openSignatureDialog = async () => {
  signatureDialogVisible.value = true
  await initSignatureCanvas()
}

const startSignature = (event) => {
  const canvas = signatureCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const { x, y } = getCanvasPoint(event)
  ctx.beginPath()
  ctx.moveTo(x, y)
  signatureDrawing.value = true
  signatureHasStroke.value = true
}

const moveSignature = (event) => {
  if (!signatureDrawing.value) return
  const canvas = signatureCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const { x, y } = getCanvasPoint(event)
  ctx.lineTo(x, y)
  ctx.stroke()
}

const endSignature = () => {
  signatureDrawing.value = false
}

const clearSignatureCanvas = () => {
  const canvas = signatureCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  signatureHasStroke.value = false
}

const handleSaveSignature = async () => {
  const canvas = signatureCanvasRef.value
  if (!canvas || !signatureHasStroke.value) {
    ElMessage.warning(t('taskDetail.noSignature'))
    return
  }
  try {
    const dataUrl = canvas.toDataURL('image/png')
    await updateTaskSignature(taskId, dataUrl)
    signatureDialogVisible.value = false
    await loadTask()
    ElMessage.success(t('common.save'))
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || t('common.save'))
  }
}

const handleDeleteSignature = async () => {
  try {
    await ElMessageBox.confirm(t('common.confirm'), t('common.delete'))
    await deleteTaskSignature(taskId)
    signatureSrc.value = ''
    await loadTask()
    ElMessage.success(t('common.delete'))
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error?.response?.data?.detail || t('common.delete'))
    }
  }
}

const handlePhotoUploadChange = async (file) => {
  const rawFile = file?.raw
  if (!rawFile) return
  try {
    await uploadTaskPhotos(taskId, [rawFile])
    await loadTask()
    ElMessage.success(t('common.upload'))
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || t('common.upload'))
  }
}

const handleDeletePhoto = async (photo) => {
  if (!photo?.id) return
  try {
    await ElMessageBox.confirm(t('common.confirm'), t('common.delete'))
    await deleteTaskPhoto(taskId, photo.id)
    await loadTask()
    ElMessage.success(t('common.delete'))
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error?.response?.data?.detail || t('common.delete'))
    }
  }
}

const handleReplacePhoto = async (photo, file) => {
  const raw = file?.raw
  if (!photo?.id || !raw) return
  try {
    await deleteTaskPhoto(taskId, photo.id)
    await uploadTaskPhotos(taskId, [raw])
    await loadTask()
    ElMessage.success(t('common.edit'))
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || t('common.edit'))
  }
}

const resetIncidentForm = () => {
  incidentForm.id = ''
  incidentForm.incident_type = ''
  incidentForm.description = ''
  incidentForm.occurred_at = ''
}

const openIncidentDialog = (row = null) => {
  resetIncidentForm()
  if (row) {
    incidentForm.id = row.id || ''
    incidentForm.incident_type = row.incident_type || ''
    incidentForm.description = row.description || ''
    incidentForm.occurred_at = row.occurred_at || ''
  }
  incidentDialogVisible.value = true
}

const handleSaveIncident = async () => {
  try {
    const payload = {
      task_id: taskId,
      incident_type: incidentForm.incident_type || null,
      description: incidentForm.description || null,
      occurred_at: incidentForm.occurred_at || null
    }
    if (incidentForm.id) {
      await updateIncidentReport(incidentForm.id, payload)
    } else {
      await createIncidentReport(payload)
    }
    incidentDialogVisible.value = false
    await loadIncidentReports()
    ElMessage.success(t('common.save'))
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || t('common.save'))
  }
}

const handleDeleteIncident = async (row) => {
  try {
    await ElMessageBox.confirm(t('common.confirm'), t('common.delete'))
    await deleteIncidentReport(row.id)
    await loadIncidentReports()
    ElMessage.success(t('common.delete'))
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(error?.response?.data?.detail || t('common.delete'))
    }
  }
}

const formatDateTime = (dateString) => {
  return formatDateTimeToMinute(dateString)
}

const normalizeTrack = (track) => {
  return {
    ...track,
    latitude: Number(track.latitude),
    longitude: Number(track.longitude),
    recorded_at: track.recorded_at || track.created_at
  }
}

const renderTrackingMap = () => {
  if (!trackingMap || trackingRecords.value.length === 0) return
  if (trackingLine) {
    trackingLine.setLatLngs([])
  }
  if (trackingMarkers) {
    trackingMarkers.clearLayers()
  }

  const latLngs = trackingRecords.value.map((item) => [item.latitude, item.longitude])
  trackingLine.setLatLngs(latLngs)
  trackingRecords.value.forEach((item) => {
    const marker = L.circleMarker([item.latitude, item.longitude], {
      radius: 4,
      color: '#409eff',
      weight: 2,
      fillColor: '#409eff',
      fillOpacity: 0.9
    })
    trackingMarkers.addLayer(marker)
  })

  if (latLngs.length === 1) {
    trackingMap.setView(latLngs[0], 15)
  } else if (latLngs.length > 1) {
    trackingMap.fitBounds(trackingLine.getBounds(), { padding: [20, 20] })
  }
}

const initTrackingMap = async () => {
  // 等待多个 tick 确保 DOM 完全渲染
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 100))
  await nextTick()
  
  if (!trackingMapRef.value) {
    console.warn('地图容器未找到，等待重试...')
    // 如果容器还没准备好，再等一会儿重试
    setTimeout(async () => {
      if (trackingMapRef.value && !trackingMap) {
        await initTrackingMap()
      }
    }, 200)
    return
  }
  
  // 检查容器是否可见且有尺寸
  const container = trackingMapRef.value
  if (container.offsetWidth === 0 || container.offsetHeight === 0) {
    console.warn('地图容器尺寸为0，等待重试...')
    setTimeout(async () => {
      if (trackingMapRef.value && !trackingMap) {
        await initTrackingMap()
      }
    }, 200)
    return
  }
  
  if (!trackingMap) {
    try {
      trackingMap = L.map(container, {
        zoomControl: true,
        attributionControl: true
      })
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
      }).addTo(trackingMap)
      trackingLine = L.polyline([], { color: '#409eff', weight: 4 })
      trackingMarkers = L.layerGroup()
      trackingLine.addTo(trackingMap)
      trackingMarkers.addTo(trackingMap)
    } catch (error) {
      console.error('地图初始化失败:', error)
      return
    }
  }
  
  // 再次等待确保地图容器可见
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 100))
  
  if (trackingRecords.value.length > 0) {
    renderTrackingMap()
  } else {
    // 即使没有数据，也要设置一个默认视图
    trackingMap.setView([39.9042, 116.4074], 10) // 北京作为默认中心
  }
  
  // 强制刷新地图尺寸
  setTimeout(() => {
    if (trackingMap) {
      trackingMap.invalidateSize()
    }
  }, 100)
}

const loadTrackingRecords = async () => {
  if (trackingLoaded.value) {
    // 数据已加载，等待容器渲染后初始化地图
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 150))
    await initTrackingMap()
    return
  }
  trackingLoading.value = true
  try {
    const result = await getTaskLocationTracks(taskId)
    const records = Array.isArray(result) ? result : []
    trackingRecords.value = records
      .map(normalizeTrack)
      .filter((item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude))
      .sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at))
    trackingLoaded.value = true
    // 等待数据更新和容器渲染
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 150))
    await initTrackingMap()
  } catch (error) {
    ElMessage.error(t('taskDetail.loadTrackingFailed'))
  } finally {
    trackingLoading.value = false
  }
}

const trackingStats = computed(() => {
  if (trackingRecords.value.length === 0) {
    return { startTime: '-', endTime: '-', durationText: '-' }
  }
  const start = trackingRecords.value[0]?.recorded_at
  const end = trackingRecords.value[trackingRecords.value.length - 1]?.recorded_at
  const startDate = start ? new Date(start) : null
  const endDate = end ? new Date(end) : null
  if (!startDate || !endDate || Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
    return {
      startTime: start ? formatDateTime(start) : '-',
      endTime: end ? formatDateTime(end) : '-',
      durationText: '-'
    }
  }
  const diffMs = Math.max(0, endDate.getTime() - startDate.getTime())
  const totalMinutes = Math.floor(diffMs / 60000)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  const durationText =
    hours > 0
      ? `${hours}${t('taskDetail.hours')}${minutes}${t('taskDetail.minutes')}`
      : `${minutes}${t('taskDetail.minutes')}`
  return {
    startTime: formatDateTime(start),
    endTime: formatDateTime(end),
    durationText
  }
})
 

watch(activeTab, async (value) => {
  if (value === 'tracking') {
    await loadTrackingRecords()
    // 如果数据已加载但地图未初始化，再次尝试初始化
    if (trackingLoaded.value && trackingRecords.value.length > 0 && !trackingMap) {
      await initTrackingMap()
    }
  }
})
onMounted(() => {
  loadTask()
  markUpdatesRead('task', taskId).catch(() => {})
})

onBeforeUnmount(() => {
  isDisposed = true
  if (trackingMap) {
    trackingMap.remove()
    trackingMap = null
  }
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
}

.loading-text {
  color: #909399;
}

.tab-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.inline-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.photo-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.photo-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.signature-dialog {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.signature-canvas {
  width: 100%;
  height: 320px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #fff;
  touch-action: none;
}

:deep(.el-descriptions) {
  --el-descriptions-item-label-font-size: var(--el-font-size-base);
  --el-descriptions-item-content-font-size: var(--el-font-size-base);
}

:deep(.el-descriptions__label),
:deep(.el-descriptions__content),
:deep(.el-descriptions__cell) {
  font-size: var(--el-font-size-base) !important;
}

:deep(.el-tabs__item) {
  font-size: var(--el-font-size-base);
}

:deep(.el-table .cell) {
  font-size: var(--el-font-size-base);
}

.incident-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.incident-item {
  margin-bottom: 8px;
}

.tracking-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tracking-map {
  width: 100%;
  height: 260px;
  min-height: 260px;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  background-color: #f5f7fa;
  position: relative;
  z-index: 0;
}

.task-record-checkboxes {
  padding: 2px 0;
}

:deep(.task-record-checkboxes .el-checkbox) {
  display: flex;
  align-items: flex-start;
  margin-right: 0;
  white-space: normal;
}

:deep(.task-record-checkboxes .el-checkbox__label) {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
