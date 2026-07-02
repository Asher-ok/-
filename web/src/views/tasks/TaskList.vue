<template>
  <div class="task-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            {{ $t('task.createTask') }}
          </el-button>
        </div>
      </template>
      
      <div class="filter-bar">
        <el-select v-model="filterStatus" :placeholder="$t('task.filterStatus')" clearable style="width: 150px" @change="handleFilterChange">
          <el-option :label="$t('task.pending')" value="pending" />
          <el-option :label="$t('task.inProgress')" value="in_progress" />
          <el-option :label="completedFilterLabel" value="completed" />
          <el-option :label="$t('task.rejected')" value="rejected" />
          <el-option :label="$t('task.approved')" value="approved" />
          <el-option :label="$t('task.cancelled')" value="cancelled" />
        </el-select>
        <el-select v-model="searchField" :placeholder="$t('task.searchCondition')" clearable style="width: 150px" @change="handleSearchFieldChange">
          <el-option :label="$t('task.customerName')" value="customer_name" />
          <el-option :label="$t('task.assignedEmployee')" value="assigned_employee" />
          <el-option :label="$t('task.title')" value="title" />
        </el-select>
        <el-select v-model="searchKeyword" :placeholder="$t('task.enterKeyword')" style="width: 240px" clearable filterable :disabled="!searchField">
          <el-option v-for="opt in searchValueOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
        <el-button type="primary" @click="handleSearch">{{ $t('task.search') }}</el-button>
        <el-button @click="handleResetSearch">{{ $t('task.reset') }}</el-button>
        <el-button @click="toggleViewMode">{{ viewMode === 'table' ? '日历展示' : '列表展示' }}</el-button>
      </div>
      
      <el-table
        v-if="viewMode === 'table'"
        :data="pagedTasks"
        v-loading="loading"
        stripe
        table-layout="auto"
        style="width: 100%"
        :default-sort="{ prop: 'service_start_time', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="status" :label="$t('task.status')" min-width="160">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" :label="$t('task.title')" min-width="260">
          <template #default="{ row }">
            <span class="clickable-with-dot">
              <span v-if="row.has_update" class="row-dot" />
              <el-link type="primary" class="clickable-text" :underline="true" @click="handleView(row)">{{ row.title || '-' }}</el-link>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="customer.name" :label="$t('task.customer')" min-width="350" />
        <el-table-column :label="$t('task.serviceItem')" min-width="350">
          <template #default="{ row }">
            <el-tooltip v-if="getTaskServiceCodes(row).length" :content="getTaskServiceCodes(row).join(', ')" placement="top">
              <span>{{ getTaskServiceCodes(row)[0] }}</span>
            </el-tooltip>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="service_start_time" column-key="service_start_time" :label="$t('task.serviceStartTime')" min-width="280" sortable="custom">
          <template #default="{ row }">
            <el-tooltip v-if="shouldHighlightDuplicateStart(row)" effect="light" placement="top">
              <template #content>
                <div class="duplicate-tip">
                  <div class="duplicate-tip__text">该客户在该服务开始时间存在多条任务</div>
                  <div class="duplicate-tip__actions">
                    <el-button type="primary" size="small" @click.stop="handleDuplicateFilter(row)">筛选</el-button>
                    <el-button size="small" @click.stop="handleDuplicateNormal(row)">正常</el-button>
                  </div>
                </div>
              </template>
              <span class="duplicate-start-time">{{ getTaskServiceStartTime(row) }}</span>
            </el-tooltip>
            <span v-else>{{ getTaskServiceStartTime(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="service_end_time" column-key="service_end_time" :label="$t('task.serviceEndTime')" min-width="280" sortable="custom">
          <template #default="{ row }">
            <span>{{ getTaskServiceEndTime(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('task.assignedEmployeeLabel')" width="170">
          <template #default="{ row }">
            <span>{{ getAssignedEmployeeName(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="filterStatus === 'pending'" :label="$t('task.overdueTime')" width="190">
          <template #default="{ row }">
            <span>{{ calculateOverdueDuration(row) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('task.operations')" width="200" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
          <template #default="{ row }">
            <div class="action-buttons action-buttons--scroll">
              <div class="action-buttons-inner">
                <el-button type="primary" plain size="small" @click="handleEdit(row)">{{ $t('task.edit') }}</el-button>
                <el-button type="danger" plain size="small" @click="handleDelete(row)">{{ $t('task.delete') }}</el-button>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-calendar v-else v-model="calendarDate" class="task-calendar">
        <template #date-cell="{ data }">
          <el-popover
            v-if="calendarTasksByDate[data.day] && calendarTasksByDate[data.day].length"
            trigger="hover"
            placement="top"
            width="520"
          >
            <template #reference>
              <div class="calendar-day calendar-day--has-tasks">
                <span class="calendar-day__num">{{ Number(data.day.split('-')[2]) }}</span>
                <span class="calendar-day__count">{{ calendarTasksByDate[data.day].length }}</span>
              </div>
            </template>
            <div class="calendar-popover">
              <div class="calendar-popover__title">
                <span>{{ data.day }}</span>
                <span class="calendar-popover__count">共 {{ calendarTasksByDate[data.day].length }} 条</span>
              </div>
              <div class="calendar-popover__list">
                <div v-for="task in getCalendarPopoverPagedTasks(data.day)" :key="task.id" class="calendar-popover__item">
                  <div class="calendar-task">
                    <div class="calendar-task__title">
                      <el-link type="primary" :underline="true" @click="handleView(task)">{{ task.title }}</el-link>
                      <el-tag size="small" :type="getStatusType(task.status)" class="calendar-task__status">{{ getStatusText(task.status) }}</el-tag>
                    </div>
                    <div class="calendar-task__meta">
                      <span class="calendar-task__meta-item">客户：{{ task.customer?.name || '-' }}</span>
                      <span class="calendar-task__meta-item">员工：{{ getAssignedEmployeeName(task) }}</span>
                    </div>
                    <div class="calendar-task__meta">
                      <span class="calendar-task__meta-item">开始：{{ getTaskServiceStartTime(task) }}</span>
                      <span class="calendar-task__meta-item">结束：{{ getTaskServiceEndTime(task) }}</span>
                    </div>
                    <div class="calendar-task__meta" v-if="getTaskServiceCodes(task).length">
                      <span class="calendar-task__meta-item">服务：{{ getTaskServiceCodes(task).join(', ') }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="calendar-popover__pager" v-if="calendarTasksByDate[data.day].length > 3">
                <el-pagination
                  small
                  :page-size="3"
                  layout="prev, pager, next"
                  :total="calendarTasksByDate[data.day].length"
                  :current-page="getCalendarPopoverPage(data.day)"
                  @current-change="(p) => setCalendarPopoverPage(data.day, p)"
                />
              </div>
            </div>
          </el-popover>
          <div v-else class="calendar-day">
            <span class="calendar-day__num">{{ Number(data.day.split('-')[2]) }}</span>
          </div>
        </template>
      </el-calendar>

      <div v-if="viewMode === 'table'" class="pager-bar">
        <el-pagination
          v-model:current-page="taskPage"
          v-model:page-size="taskPageSize"
          :page-sizes="[10]"
          layout="total, prev, pager, next"
          :total="taskTotal"
        />
      </div>
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="760px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="auto" class="task-form">
        <el-form-item :label="$t('task.title')" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item :label="$t('task.description')" prop="description">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item :label="$t('task.customer')" prop="customer_id">
          <el-select v-model="form.customer_id" :placeholder="$t('task.selectCustomer')" style="width: 100%" @change="handleCustomerChange">
            <el-option v-for="customer in customers" :key="customer.id" :label="customer.name" :value="customer.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('task.assignedEmployeeLabel')" prop="assigned_employee_id">
          <el-select v-model="form.assigned_employee_id" :placeholder="$t('task.selectEmployee')" style="width: 100%" @change="handleAssignedEmployeeChange">
            <el-option
              v-for="employee in employees"
              :key="employee.id"
              :label="`${employee.name}（${employee.employee_number}）`"
              :value="employee.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('task.questionnaire')">
          <div style="width: 100%">
            <el-button type="primary" size="small" @click="addQuestionnaireRow" style="margin-bottom: 10px">
              <el-icon><Plus /></el-icon>{{ $t('task.addQuestionnaire') }}
            </el-button>
            <el-table v-if="form.questionnaires.length" :data="form.questionnaires" size="small" stripe style="width: 100%">
              <el-table-column :label="$t('task.questionnaireTitle')">
                <template #default="{ row }">
                  <el-select v-model="row.questionnaire_id" :placeholder="$t('task.selectQuestionnaire')" style="width: 100%" clearable filterable>
                    <el-option v-for="q in questionnaires" :key="q.id" :label="q.title" :value="q.id" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column :label="$t('task.isRequired')" width="100" align="center">
                <template #default="{ row }">
                  <el-switch v-model="row.is_required" />
                </template>
              </el-table-column>
              <el-table-column :label="$t('common.operations')" width="100" align="center">
                <template #default="{ $index }">
                  <el-button type="danger" circle size="small" @click="removeQuestionnaireRow($index)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-form-item>
        <el-form-item :label="$t('task.incidentTemplate')">
          <el-select v-model="form.incident_template_id" :placeholder="$t('task.selectIncidentTemplate')" style="width: 100%" clearable filterable>
            <el-option v-for="tpl in incidentTemplates" :key="tpl.id" :label="tpl.title" :value="tpl.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('task.taskRecordTemplate')">
          <el-select v-model="form.task_record_template_id" :placeholder="$t('task.selectTaskRecordTemplate')" style="width: 100%" clearable filterable>
            <el-option v-for="tpl in taskRecordTemplates" :key="tpl.id" :label="tpl.title" :value="tpl.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!editingTaskId" :label="$t('task.repeatRule')" prop="repeat_rule">
          <el-select v-model="form.repeat_rule" :placeholder="$t('task.selectRepeatRule')" style="width: 100%" clearable>
            <el-option :label="$t('task.repeatWeekly')" value="weekly" />
            <el-option :label="$t('task.repeatSingleWeek')" value="single_week" />
            <el-option :label="$t('task.repeatDoubleWeek')" value="double_week" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!editingTaskId && form.repeat_rule" :label="$t('task.repeatMonths')" prop="repeat_months">
          <el-select v-model="form.repeat_months" :placeholder="$t('task.selectRepeatMonths')" style="width: 100%">
            <el-option v-for="m in 24" :key="m" :label="t('task.repeatMonthsOption', { months: m })" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('task.services')" required>
          <div style="width: 100%">
            <el-button type="primary" @click="openServiceDialog()">{{ $t('task.addService') }}</el-button>
            <el-table v-if="form.services.length" :data="form.services" size="small" stripe style="width: 100%; margin-top: 10px">
              <el-table-column prop="service_code" :label="$t('task.serviceCode')" min-width="160" />
              <el-table-column prop="unit_price" :label="$t('task.unitPrice')" width="120">
                <template #default="{ row }">
                  <span>${{ formatAmount(row.unit_price) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="duration_hours" :label="$t('task.serviceDurationHours')" width="140">
                <template #default="{ row }">
                  <span>{{ row.duration_hours }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="total_price" :label="$t('task.totalPrice')" width="140">
                <template #default="{ row }">
                  <span class="task-total-price">${{ formatAmount(row.total_price) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="service_time_start" :label="$t('task.serviceStartTime')" width="170">
                <template #default="{ row }">
                  <span>{{ formatTaskDisplayTime(row.service_time_start) || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="service_time_end" :label="$t('task.serviceEndTime')" width="170">
                <template #default="{ row }">
                  <span>{{ formatTaskDisplayTime(row.service_time_end) || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="latest_claim_time" :label="$t('task.latestClaimTime')" width="170">
                <template #default="{ row }">
                  <span>{{ formatTaskDisplayTime(row.latest_claim_time) || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column :label="$t('common.operations')" width="140" :fixed="isMobile ? false : 'right'">
                <template #default="{ $index }">
                  <el-button size="small" @click="openServiceDialog($index)">{{ $t('common.edit') }}</el-button>
                  <el-button size="small" type="danger" @click="removeServiceItem($index)">{{ $t('common.delete') }}</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else :description="$t('task.noServices')" />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="serviceDialogVisible" :title="serviceDialogTitle" width="760px" :close-on-click-modal="false">
      <el-form :model="serviceForm" :rules="serviceRules" ref="serviceFormRef" label-position="top">
        <el-form-item label="选择服务" prop="service_path">
          <el-cascader
            v-model="serviceForm.service_path"
            :options="serviceCascaderOptions"
            :props="serviceCascaderProps"
            :placeholder="$t('task.selectServiceLevel3')"
            clearable
            filterable
            style="width: 100%"
            @change="handleServiceCascaderChange"
          />
        </el-form-item>

        <el-form-item v-if="serviceForm.level3_id" :label="$t('task.serviceCode')" prop="service_code_id">
          <el-select
            v-model="serviceForm.service_code_id"
            :placeholder="$t('task.selectServiceCode')"
            style="width: 100%"
            filterable
            @change="handleServiceCodeChange"
          >
            <el-option v-for="opt in serviceCodeOptions" :key="opt.id" :label="opt.displayLabel" :value="opt.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('task.unitPrice')" prop="unit_price">
          <el-input-number v-model="serviceForm.unit_price" :min="0.01" :precision="2" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="$t('task.serviceDurationHours')" prop="duration_hours">
          <el-input-number v-model="serviceForm.duration_hours" :min="0.01" :precision="2" :step="0.5" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="$t('task.totalPrice')">
          <span class="task-total-price">${{ formatAmount(serviceTotalPrice) }}</span>
        </el-form-item>
        <el-form-item label="服务开始日期" prop="service_start_date">
          <el-date-picker v-model="serviceForm.service_start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item label="服务开始时间" prop="service_start_time">
          <el-time-picker
            v-model="serviceForm.service_start_time"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
            clearable
            @change="markServiceStartTimeTouched"
          />
        </el-form-item>
        <el-form-item :label="$t('task.serviceEndTime')" prop="service_time_end">
          <el-date-picker
            v-model="serviceForm.service_time_end"
            type="datetime"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
            clearable
            @change="markServiceEndTimeTouched"
          />
        </el-form-item>
        <el-form-item :label="$t('task.latestClaimTime')" prop="latest_claim_time">
          <el-date-picker
            v-model="serviceForm.latest_claim_time"
            type="datetime"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
            clearable
            @change="markServiceClaimTimeTouched"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serviceDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveServiceItem">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({
  name: 'Tasks'
})
import { ref, reactive, onMounted, computed, watch, nextTick, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getTasks,
  getTask,
  createTask,
  updateTask,
  approveTask,
  rejectTask,
  deleteTask,
  cancelTask,
  addTaskService,
  updateTaskService,
  deleteTaskService,
  getTaskServices,
  getCustomerServiceLevel1,
  getCustomerServiceLevel2,
  getCustomerServiceLevel3,
  getCustomerServiceCodes
} from '@/api/tasks'
import { getCustomers, getCustomer } from '@/api/customers'
import { getEmployees } from '@/api/employees'
import { getServiceLevel1, getServiceLevel2, getServiceLevel3, getServiceCodes } from '@/api/invoices'
import { getQuestionnaires } from '@/api/questionnaires'
import { getIncidentTemplates } from '@/api/incidentTemplates'
import { getTaskRecordTemplates } from '@/api/taskRecordTemplates'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { formatDateTimeToMinute } from '@/utils/formatters'
import { markUpdatesRead } from '@/api/updates'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))
const route = useRoute()
const router = useRouter()

const pageTitle = computed(() => {
  const base = t('menu.tasks')
  if (route.path.endsWith('/tasks/all')) return `${base}/${t('invoice.allTab')}`
  return base
})
const tasks = ref([])
const searchCandidateRows = ref([])
const taskPage = ref(1)
const taskPageSize = ref(10)
const viewMode = ref('table')
const calendarDate = ref(new Date())
const customers = ref([])
const employees = ref([])
const questionnaires = ref([])
const incidentTemplates = ref([])
const taskRecordTemplates = ref([])
const loading = ref(false)
const filterStatus = ref('')
const searchField = ref('')
const searchKeyword = ref('')
const sortState = reactive({
  prop: 'service_start_time',
  order: 'descending'
})
const duplicateFilter = ref(null)
const suppressedDuplicateKeys = ref({})
const dialogVisible = ref(false)
const formRef = ref(null)
const editingTaskId = ref('')
const serviceDialogVisible = ref(false)
const serviceFormRef = ref(null)
const serviceEditingIndex = ref(-1)
const originalServiceIds = ref([])
const originalServicesFingerprint = ref('')
const customerAcceptedLevel1Ids = ref([])
const suppressCustomerWatch = ref(false)
const suppressEmployeeNotice = ref(false)
const serviceLevel1Options = ref([])
const serviceCodeOptions = ref([])
const serviceCascaderOptions = ref([])
const selectedServiceCascaderPath = ref([])

const parseAmount = (value) => {
  if (value == null) return null
  if (typeof value === 'number') return isNaN(value) ? null : value
  if (typeof value === 'string') {
    const s = value.trim()
    if (!s) return null
    const n = Number(s)
    return isNaN(n) ? null : n
  }
  if (typeof value === 'object') {
    const v = value?.value ?? value?.amount ?? value?.unit_price ?? value?.price ?? null
    return parseAmount(v)
  }
  return null
}

const dialogTitle = computed(() => {
  return editingTaskId.value ? t('task.editTask') : t('task.createTask')
})

const completedFilterLabel = computed(() => `${t('task.completed')}（未审核）`)

const toggleViewMode = () => {
  viewMode.value = viewMode.value === 'table' ? 'calendar' : 'table'
}

const toMinuteKey = (value) => {
  const s = normalizeString(value)
  if (!s) return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
  const m = s.replace('T', ' ').match(/^(\d{4}-\d{2}-\d{2})[ ](\d{2}:\d{2})/)
  if (m) return `${m[1]} ${m[2]}`
  return ''
}

const getRowCustomerId = (row) => row?.customer_id || row?.customer?.id || ''

const getRowServiceStartKey = (row) => {
  const raw = row?.service_start_time || row?.service_time || ''
  const direct = toMinuteKey(raw)
  if (direct) return direct
  const list = Array.isArray(row?.services)
    ? row.services
    : (Array.isArray(row?.service_items) ? row.service_items : (Array.isArray(row?.service_lines) ? row.service_lines : []))
  const keys = list.map((s) => toMinuteKey(s?.service_time_start || s?.service_start_time || '')).filter(Boolean).sort()
  return keys.length ? keys[0] : ''
}

const getRowServiceEndKey = (row) => {
  const raw = row?.service_end_time || ''
  const direct = toMinuteKey(raw)
  if (direct) return direct
  const list = Array.isArray(row?.services)
    ? row.services
    : (Array.isArray(row?.service_items) ? row.service_items : (Array.isArray(row?.service_lines) ? row.service_lines : []))
  const keys = list.map((s) => toMinuteKey(s?.service_time_end || s?.service_end_time || '')).filter(Boolean).sort()
  return keys.length ? keys[keys.length - 1] : ''
}

const toTimestamp = (minuteKey) => {
  const s = normalizeString(minuteKey)
  if (!s) return 0
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    const d = new Date(`${s}T00:00:00`)
    const n = d.getTime()
    return Number.isNaN(n) ? 0 : n
  }
  const d = new Date(s.replace(' ', 'T') + ':00')
  const n = d.getTime()
  return Number.isNaN(n) ? 0 : n
}

const getDuplicateGroupKey = (row) => {
  const customerId = getRowCustomerId(row)
  const startKey = getRowServiceStartKey(row)
  if (!customerId || !startKey) return ''
  return `${customerId}::${startKey}`
}

const duplicateLateTaskIds = computed(() => {
  const list = Array.isArray(tasks.value) ? tasks.value : []
  const groups = new Map()
  for (const row of list) {
    const key = getDuplicateGroupKey(row)
    if (!key) continue
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key).push(row)
  }
  const set = new Set()
  for (const [_, rows] of groups) {
    if (rows.length <= 1) continue
    const sorted = [...rows].sort((a, b) => {
      const at = new Date(normalizeString(a?.created_at)).getTime() || 0
      const bt = new Date(normalizeString(b?.created_at)).getTime() || 0
      return at - bt
    })
    for (let i = 1; i < sorted.length; i++) {
      if (sorted[i]?.id) set.add(sorted[i].id)
    }
  }
  return set
})

const isSuppressedDuplicateKey = (key) => !!suppressedDuplicateKeys.value?.[key]

const shouldHighlightDuplicateStart = (row) => {
  const id = row?.id
  if (!id) return false
  if (!duplicateLateTaskIds.value.has(id)) return false
  const key = getDuplicateGroupKey(row)
  if (!key) return false
  return !isSuppressedDuplicateKey(key)
}

const handleDuplicateNormal = (row) => {
  const key = getDuplicateGroupKey(row)
  if (!key) return
  suppressedDuplicateKeys.value = { ...(suppressedDuplicateKeys.value || {}), [key]: true }
  if (duplicateFilter.value?.key === key) {
    duplicateFilter.value = null
  }
}

const handleDuplicateFilter = async (row) => {
  const key = getDuplicateGroupKey(row)
  const customerId = getRowCustomerId(row)
  const startKey = getRowServiceStartKey(row)
  if (!key || !customerId || !startKey) return
  viewMode.value = 'table'
  await handleResetSearch()
  duplicateFilter.value = { key, customerId, startKey }
}

const handleSortChange = ({ prop, order }) => {
  sortState.prop = prop || ''
  sortState.order = order
  taskPage.value = 1
}

const tasksViewList = computed(() => {
  let list = Array.isArray(tasks.value) ? [...tasks.value] : []

  if (duplicateFilter.value?.key) {
    const { customerId, startKey } = duplicateFilter.value
    list = list.filter((row) => getRowCustomerId(row) === customerId && getRowServiceStartKey(row) === startKey)
  }

  const { prop, order } = sortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1

  if (prop === 'service_start_time') {
    return list.sort((a, b) => (toTimestamp(getRowServiceStartKey(a)) - toTimestamp(getRowServiceStartKey(b))) * dir)
  }
  if (prop === 'service_end_time') {
    return list.sort((a, b) => (toTimestamp(getRowServiceEndKey(a)) - toTimestamp(getRowServiceEndKey(b))) * dir)
  }
  return list
})

const taskTotal = computed(() => (Array.isArray(tasksViewList.value) ? tasksViewList.value.length : 0))

const pagedTasks = computed(() => {
  const list = Array.isArray(tasksViewList.value) ? tasksViewList.value : []
  const page = Number(taskPage.value) || 1
  const size = Number(taskPageSize.value) || 10
  const start = (page - 1) * size
  return list.slice(start, start + size)
})

const calendarTasksByDate = computed(() => {
  const map = {}
  const list = Array.isArray(tasksViewList.value) ? tasksViewList.value : []
  for (const row of list) {
    const startKey = getRowServiceStartKey(row)
    const day = startKey ? startKey.slice(0, 10) : ''
    if (!day) continue
    if (!map[day]) map[day] = []
    map[day].push(row)
  }
  Object.keys(map).forEach((day) => {
    map[day].sort((a, b) => {
      const at = toTimestamp(getRowServiceStartKey(a))
      const bt = toTimestamp(getRowServiceStartKey(b))
      return at - bt
    })
  })
  return map
})

const calendarPopoverPageByDay = ref({})
const calendarPopoverPageSize = 3

const getCalendarPopoverPage = (day) => {
  const key = normalizeString(day)
  if (!key) return 1
  const raw = calendarPopoverPageByDay.value?.[key]
  const page = Number(raw) || 1
  return page < 1 ? 1 : page
}

const setCalendarPopoverPage = (day, page) => {
  const key = normalizeString(day)
  if (!key) return
  const total = Array.isArray(calendarTasksByDate.value?.[key]) ? calendarTasksByDate.value[key].length : 0
  const maxPage = Math.max(1, Math.ceil(total / calendarPopoverPageSize))
  const next = Math.min(Math.max(1, Number(page) || 1), maxPage)
  calendarPopoverPageByDay.value = { ...(calendarPopoverPageByDay.value || {}), [key]: next }
}

const getCalendarPopoverPagedTasks = (day) => {
  const key = normalizeString(day)
  const list = Array.isArray(calendarTasksByDate.value?.[key]) ? calendarTasksByDate.value[key] : []
  const page = getCalendarPopoverPage(key)
  const start = (page - 1) * calendarPopoverPageSize
  return list.slice(start, start + calendarPopoverPageSize)
}

const form = reactive({
  title: '',
  description: '',
  customer_id: '',
  assigned_employee_id: '',
  questionnaire_id: '',
  incident_template_id: '',
  task_record_template_id: '',
  questionnaires: [],
  repeat_rule: '',
  repeat_months: null,
  services: []
})

const rules = {
  title: [{ required: true, message: t('task.titleRequired'), trigger: 'blur' }],
  customer_id: [{ required: true, message: t('task.customerRequired'), trigger: 'change' }],
  assigned_employee_id: [{ required: true, message: t('task.employeeRequired'), trigger: 'change' }]
}

const handleAssignedEmployeeChange = (employeeId) => {
  if (suppressEmployeeNotice.value) return
  const id = employeeId || form.assigned_employee_id
  if (!id) return
  const emp = employees.value.find((e) => e.id === id)
  if (!emp) return
  const hours = emp.weekly_served_hours != null ? Number(emp.weekly_served_hours).toFixed(2) : '0.00'
  console.log('Employee change:', { id, emp, hours })
  const msg = t('task.employeeWeeklyServedHoursNotice', { hours })
  console.log('Message content:', msg)
  ElMessage.info({
    message: msg,
    duration: 4500
  })
}

const handleCustomerChange = (customerId) => {
  const id = customerId || form.customer_id
  if (!id) return
  const customer = customers.value.find((c) => c.id === id)
  if (!customer) return
  const hours = customer.weekly_served_hours != null ? Number(customer.weekly_served_hours).toFixed(2) : '0.00'
  console.log('Customer change:', { id, customer, hours })
  const msg = t('task.customerWeeklyServedHoursNotice', { hours })
  console.log('Message content:', msg)
  ElMessage.info({
    message: msg,
    duration: 2000
  })
}

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

const normalizeString = (value) => (value == null ? '' : String(value)).trim()

const toFingerprintNumber = (value) => {
  if (value == null) return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

const buildServicesFingerprint = (services) => {
  const list = Array.isArray(services) ? services : []
  const normalized = list.map((s, index) => ({
    id: normalizeString(s?.id || '') || `__new__${index}`,
    level1_id: normalizeString(s?.level1_id || ''),
    level2_id: normalizeString(s?.level2_id || ''),
    level3_id: normalizeString(s?.level3_id || ''),
    service_code: normalizeString(s?.service_code || ''),
    duration_hours: toFingerprintNumber(s?.duration_hours),
    unit_price: toFingerprintNumber(s?.unit_price),
    service_time_start: normalizeString(s?.service_time_start || ''),
    service_time_end: normalizeString(s?.service_time_end || '')
  }))
  normalized.sort((a, b) => String(a.id).localeCompare(String(b.id)))
  return JSON.stringify(normalized)
}

const loadSearchCandidates = async () => {
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    searchCandidateRows.value = await getTasks(params)
  } catch {
    searchCandidateRows.value = []
  }
}

const searchValueOptions = computed(() => {
  const field = normalizeString(searchField.value)
  const rows = Array.isArray(searchCandidateRows.value) ? searchCandidateRows.value : []
  if (!field) return []

  if (field === 'customer_name') {
    const names = rows
      .map((r) => r?.customer?.name || r?.customer_name || '')
      .map((s) => normalizeString(s))
      .filter(Boolean)
    const uniq = Array.from(new Set(names)).sort((a, b) => a.localeCompare(b))
    return uniq.map((name) => ({ label: name, value: name }))
  }

  if (field === 'title') {
    const titles = rows
      .map((r) => r?.title || '')
      .map((s) => normalizeString(s))
      .filter(Boolean)
    const uniq = Array.from(new Set(titles)).sort((a, b) => a.localeCompare(b))
    return uniq.map((title) => ({ label: title, value: title }))
  }

  if (field === 'assigned_employee') {
    const employeeById = new Map((employees.value || []).map((e) => [e.id, e]))
    const rawIds = rows.map((r) => r?.assigned_employee_id).filter(Boolean)
    const uniqIds = Array.from(new Set(rawIds))
    const opts = uniqIds
      .map((id) => {
        const emp = employeeById.get(id)
        const name = normalizeString(emp?.name || '')
        const num = normalizeString(emp?.employee_number || '')
        const label = name && num ? `${name}（${num}）` : (name || num)
        const value = num || name
        return label && value ? { label, value } : null
      })
      .filter(Boolean)
    opts.sort((a, b) => a.label.localeCompare(b.label))
    return opts
  }

  return []
})

const handleFilterChange = async () => {
  duplicateFilter.value = null
  taskPage.value = 1
  await Promise.all([loadSearchCandidates(), loadTasks()])
}

const handleSearchFieldChange = async () => {
  duplicateFilter.value = null
  searchKeyword.value = ''
  taskPage.value = 1
}

const serviceDialogTitle = computed(() => {
  return serviceEditingIndex.value >= 0 ? t('task.editService') : t('task.addService')
})

const serviceStartTimeTouched = ref(false)
const serviceEndTimeTouched = ref(false)
const serviceClaimTimeTouched = ref(false)

const markServiceStartTimeTouched = () => {
  serviceStartTimeTouched.value = true
}
const markServiceEndTimeTouched = () => {
  serviceEndTimeTouched.value = true
}
const markServiceClaimTimeTouched = () => {
  serviceClaimTimeTouched.value = true
}

const serviceForm = reactive({
  service_path: [],
  level1_id: '',
  level2_id: '',
  level3_id: '',
  service_code_id: '',
  service_code: '',
  unit_price: null,
  duration_hours: null,
  service_start_date: '',
  service_start_time: '',
  service_time_start: '',
  service_time_end: '',
  latest_claim_time: ''
})

const serviceRules = {
  service_path: [
    {
      validator: (_, value, callback) => {
        const list = Array.isArray(value) ? value.filter(Boolean) : []
        if (list.length < 2) callback(new Error(t('task.selectServiceLevel3')))
        else callback()
      },
      trigger: 'change'
    }
  ],
  service_code_id: [{ required: true, message: t('task.selectServiceCode'), trigger: 'change' }],
  unit_price: [{ required: true, message: t('task.unitPriceRequired'), trigger: 'change' }],
  duration_hours: [{ required: true, message: t('task.durationRequired'), trigger: 'change' }],
  service_start_date: [{ required: true, message: t('task.serviceStartTimeRequired'), trigger: 'change' }]
}

const serviceTotalPrice = computed(() => {
  const hours = Number(serviceForm.duration_hours) || 0
  const price = Number(serviceForm.unit_price) || 0
  if (hours <= 0 || price <= 0) return 0
  return Number((hours * price).toFixed(2))
})

const parseDateTimeLocal = (value) => {
  if (!value || typeof value !== 'string') return null
  const s = value.trim()
  if (!s) return null
  const d = new Date(s.replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return null
  return d
}

const normalizeDateTimeValue = (value) => {
  if (!value) return ''
  const s = String(value).trim()
  if (!s) return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
  if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}$/.test(s)) return `${s}:00`
  return s
}

const splitDateTimeParts = (value) => {
  const raw = normalizeDateTimeValue(value)
  if (!raw) return { date: '', time: '', raw: '' }
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return { date: raw, time: '', raw }
  const m = raw.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/)
  if (!m) return { date: '', time: '', raw }
  return { date: m[1], time: m[2], raw }
}

const formatDateTimeLocal = (date) => {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const applyDerivedServiceTimes = () => {
  const date = normalizeString(serviceForm.service_start_date)
  const time = normalizeString(serviceForm.service_start_time)
  const hours = Number(serviceForm.duration_hours)

  if (!date) {
    serviceForm.service_time_start = ''
    if (!serviceEndTimeTouched.value) serviceForm.service_time_end = ''
    if (!serviceClaimTimeTouched.value) serviceForm.latest_claim_time = ''
    return
  }

  if (!time) {
    serviceForm.service_time_start = date
    if (!serviceEndTimeTouched.value) serviceForm.service_time_end = ''
    if (!serviceClaimTimeTouched.value) serviceForm.latest_claim_time = ''
    return
  }

  const start = parseDateTimeLocal(`${date} ${time}:00`)
  if (!start) return
  serviceForm.service_time_start = formatDateTimeLocal(start)

  if (!serviceClaimTimeTouched.value) serviceForm.latest_claim_time = ''

  if (!serviceEndTimeTouched.value && Number.isFinite(hours) && hours > 0) {
    const end = new Date(start.getTime() + Math.round(hours * 60 * 60 * 1000))
    serviceForm.service_time_end = formatDateTimeLocal(end)
  } else if (!serviceEndTimeTouched.value) {
    serviceForm.service_time_end = ''
  }
}

watch(
  () => [serviceForm.service_start_date, serviceForm.service_start_time, serviceForm.duration_hours],
  () => {
    applyDerivedServiceTimes()
  },
  { deep: true }
)

const filteredLevel1Options = computed(() => {
  const allow = new Set(customerAcceptedLevel1Ids.value || [])
  if (!allow.size) return serviceLevel1Options.value
  return serviceLevel1Options.value.filter((o) => allow.has(o.id))
})

const getArrayFromResponse = (res) => {
  if (Array.isArray(res)) return res
  const candidates = [
    res?.rows,
    res?.items,
    res?.data,
    res?.data?.rows,
    res?.data?.items,
    res?.data?.data,
    res?.result,
    res?.result?.rows,
    res?.result?.items
  ]
  for (const item of candidates) {
    if (Array.isArray(item)) return item
  }
  return []
}

const formatAmount = (val) => {
  const n = Number(val || 0)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(2)
}

const formatTaskDisplayTime = (value) => {
  const s = normalizeString(value)
  if (!s) return ''
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
  const formatted = formatDateTimeToMinute(s)
  if (!formatted) return s
  if (formatted.endsWith(' 00:00')) {
    return formatted.slice(0, 10)
  }
  return formatted
}

const getTaskServiceCodes = (row) => {
  const rawList = Array.isArray(row?.services)
    ? row.services
    : (Array.isArray(row?.service_items) ? row.service_items : (Array.isArray(row?.service_lines) ? row.service_lines : []))
  const codes = rawList
    .map((s) => s?.service_code || s?.code || s?.serviceCode || '')
    .filter(Boolean)
  const fallback = row?.service_code ? [row.service_code] : []
  const normalized = (codes.length ? codes : fallback).map((c) => String(c).trim()).filter(Boolean)
  return Array.from(new Set(normalized))
}

const getTaskServiceStartTime = (row) => {
  if (row?.service_start_time || row?.service_time) return formatTaskDisplayTime(row.service_start_time || row.service_time)
  const list = Array.isArray(row?.services) ? row.services : []
  const times = list.map((s) => s?.service_time_start || s?.service_start_time).filter(Boolean)
  if (!times.length) return '-'
  times.sort()
  return formatTaskDisplayTime(times[0])
}

const getTaskServiceEndTime = (row) => {
  if (row?.service_end_time) return formatTaskDisplayTime(row.service_end_time)
  const list = Array.isArray(row?.services) ? row.services : []
  const times = list.map((s) => s?.service_time_end || s?.service_end_time).filter(Boolean)
  if (!times.length) return '-'
  times.sort()
  return formatTaskDisplayTime(times[times.length - 1])
}

const loadTasks = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    const keyword = normalizeString(searchKeyword.value)
    if (keyword && searchField.value) {
      params.field = searchField.value
      params.keyword = keyword
    }
    tasks.value = await getTasks(params)
    taskPage.value = 1
  } catch (error) {
    ElMessage.error(t('task.loadTasksFailed'))
  } finally {
    loading.value = false
  }
}

const loadCustomers = async () => {
  try {
    customers.value = await getCustomers()
  } catch (error) {
    ElMessage.error(t('task.loadCustomersFailed'))
  }
}

const loadEmployees = async () => {
  try {
    employees.value = await getEmployees()
  } catch (error) {
    ElMessage.error(t('task.loadEmployeesFailed'))
  }
}

const loadQuestionnaires = async () => {
  try {
    const res = await getQuestionnaires()
    const rows = getArrayFromResponse(res)
    questionnaires.value = rows.map((q) => ({ id: q.id, title: q.title || q.name || '' })).filter((i) => i.id && i.title)
  } catch (error) {
    questionnaires.value = []
  }
}

const loadIncidentTemplates = async () => {
  try {
    const res = await getIncidentTemplates()
    const rows = getArrayFromResponse(res)
    incidentTemplates.value = rows
      .filter((r) => r && r.id && r.is_active !== false)
      .map((r) => ({ id: r.id, title: r.title || r.name || '' }))
  } catch (error) {
    incidentTemplates.value = []
  }
}

const loadTaskRecordTemplates = async () => {
  try {
    const res = await getTaskRecordTemplates()
    const rows = getArrayFromResponse(res)
    taskRecordTemplates.value = rows
      .filter((r) => r && r.id && r.is_active !== false)
      .map((r) => ({ id: r.id, title: r.title || r.name || '' }))
  } catch (error) {
    taskRecordTemplates.value = []
  }
}

const handleAdd = async () => {
  editingTaskId.value = ''
  originalServiceIds.value = []
  originalServicesFingerprint.value = ''
  suppressCustomerWatch.value = true
  suppressEmployeeNotice.value = true
  Object.assign(form, {
    title: '',
    description: '',
    customer_id: '',
    assigned_employee_id: '',
    questionnaire_id: '',
    incident_template_id: '',
    task_record_template_id: '',
    questionnaires: [],
    repeat_rule: '',
    repeat_months: null,
    services: []
  })
  customerAcceptedLevel1Ids.value = []
  suppressCustomerWatch.value = false
  suppressEmployeeNotice.value = false
  dialogVisible.value = true
  await loadCustomers()
}

const handleView = (row) => {
  if (row?.has_update && row?.id) {
    markUpdatesRead('task', row.id).catch(() => {})
    row.has_update = false
  }
  router.push(`/tasks/${row.id}`)
}

const handleEdit = async (row) => {
  loading.value = true
  try {
    const detail = await getTask(row.id)
    editingTaskId.value = detail.id
    suppressCustomerWatch.value = true
    suppressEmployeeNotice.value = true
    originalServiceIds.value = []
    Object.assign(form, {
      title: detail.title || '',
      description: detail.description || '',
      customer_id: detail.customer_id || '',
      assigned_employee_id: detail.assigned_employee_id || '',
      questionnaire_id: detail.questionnaire_id || '',
      incident_template_id: detail.incident_template_id || '',
      task_record_template_id: detail.task_record_template_id || '',
      questionnaires: (detail.task_questionnaires || []).map((q) => ({
        questionnaire_id: q.questionnaire_id,
        is_required: q.is_required,
        order_index: q.order_index
      })),
      repeat_rule: '',
      repeat_months: null,
    services: (Array.isArray(detail.services) ? detail.services : (Array.isArray(detail.service_items) ? detail.service_items : []))
      .map((s) => {
        const unit = parseAmount(s.unit_price_override ?? s.unit_price ?? s.unitPrice ?? s.price)
        const hours =
          s.duration_hours != null
            ? Number(s.duration_hours)
            : (s.service_duration_hours != null
                ? Number(s.service_duration_hours)
                : (s.duration != null
                    ? Number(s.duration)
                    : (s.hours != null ? Number(s.hours) : (s.quantity != null ? Number(s.quantity) : null))))
        let total = null
        if (s.total_price != null) total = Number(s.total_price)
        else if (s.amount != null) total = Number(s.amount)
        else if (s.total_amount != null) total = Number(s.total_amount)
        else if (s.line_total != null) total = Number(s.line_total)
        else if (s.total != null) total = Number(s.total)
        else if (unit != null && hours != null) total = Number((unit * hours).toFixed(2))

        const itemId = s.task_service_item_id ?? s.taskServiceItemId ?? s.item_id ?? s.itemId ?? s.id ?? ''
        const serviceCodeId = s.service_code_id ?? s.serviceCodeId ?? s.code_id ?? s.codeId ?? ''

        return {
          id: itemId,
          level1_id: s.level1_id || s.service_level1_id || '',
          level1_name: s.level1_name || s.service_level1_name || '',
          level2_id: s.level2_id || s.service_level2_id || '',
          level2_name: s.level2_name || s.service_level2_name || '',
          level3_id: s.level3_id || s.service_level3_id || '',
          level3_name: s.level3_name || s.service_level3_name || '',
          service_code_id: serviceCodeId,
          service_code: s.service_code || s.code || '',
          unit_price: unit,
          duration_hours: hours,
          total_price: total,
          service_time_start: s.service_time_start || s.service_start_time || '',
          service_time_end: s.service_time_end || s.service_end_time || '',
          latest_claim_time: s.latest_claim_time || ''
        }
      })
    })
    originalServiceIds.value = (Array.isArray(form.services) ? form.services : []).map((it) => it?.id).filter(Boolean)
    originalServicesFingerprint.value = buildServicesFingerprint(form.services)
    await nextTick()
    suppressCustomerWatch.value = false
    suppressEmployeeNotice.value = false
    await loadCustomerAcceptedLevel1(form.customer_id)
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

const getAssignedEmployeeName = (row) => {
  if (!row.assigned_employee_id) return t('task.allEmployees')
  const matched = employees.value.find((employee) => employee.id === row.assigned_employee_id)
  return matched ? matched.name : t('task.allEmployees')
}

const calculateOverdueDuration = (row) => {
  // 使用后端返回的 overdue_duration，如果不存在则前端计算
  if (row.overdue_duration) return row.overdue_duration
  
  if (!row.latest_claim_time) return null
  if (row.status !== 'pending') return null
  
  const now = new Date()
  const claimTime = new Date(row.latest_claim_time)
  if (claimTime >= now) return null // 未超时
  
  const diff = now - claimTime
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (days > 0) return `${t('task.overdue')} ${days}天${hours}小时`
  if (hours > 0) return `${t('task.overdue')} ${hours}小时${minutes}分钟`
  return `${t('task.overdue')} ${minutes}分钟`
}

const handleApprove = async (row) => {
  try {
    const result = await approveTask(row.id)
    console.log('审核通过结果:', result)
    ElMessage.success(t('task.approveSuccess'))
    await loadTasks()
  } catch (error) {
    console.error('审核通过失败:', error)
    ElMessage.error(getErrorMessage(error))
  }
}

const handleReject = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt(t('task.rejectPrompt'), t('task.rejectTitle'), {
      inputType: 'textarea'
    })
    const result = await rejectTask(row.id, value)
    console.log('审核拒绝结果:', result)
    ElMessage.success(t('task.rejectSuccess'))
    await loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('审核拒绝失败:', error)
      ElMessage.error(getErrorMessage(error))
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('task.deleteConfirm'), t('task.tip'), { type: 'warning' })
    const taskId = row?.id ?? row?.task_id ?? row?.taskId
    if (!taskId) {
      ElMessage.error(t('task.operationFailed'))
      return
    }
    const params = {}
    const sourceTaskId = row?.source_task_id ?? row?.sourceTaskId
    if (sourceTaskId) params.source_task_id = sourceTaskId
    await deleteTask(taskId, Object.keys(params).length ? params : undefined)
    ElMessage.success(t('task.deleteSuccess'))
    loadTasks()
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getErrorMessage(error))
    }
  }
}

const handleCancel = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt(t('task.cancelPrompt'), t('task.cancelTitle'), {
      inputType: 'textarea'
    })
    const result = await cancelTask(row.id, value)
    console.log('取消任务结果:', result)
    ElMessage.success(t('task.cancelSuccess'))
    await loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error(getErrorMessage(error))
    }
  }
}

const handleSearch = async () => {
  duplicateFilter.value = null
  taskPage.value = 1
  await loadTasks()
}

const handleResetSearch = async () => {
  filterStatus.value = ''
  searchField.value = ''
  searchKeyword.value = ''
  duplicateFilter.value = null
  taskPage.value = 1
  await Promise.all([loadSearchCandidates(), loadTasks()])
}

const addQuestionnaireRow = () => {
  form.questionnaires.push({
    questionnaire_id: '',
    is_required: true,
    order_index: form.questionnaires.length
  })
}

const removeQuestionnaireRow = (index) => {
  form.questionnaires.splice(index, 1)
}

const getErrorMessage = (error) => {
  if (!error) return t('task.operationFailed')
  const detail = error.response?.data?.detail
  if (detail) return detail
  const message = error.response?.data?.message || error.message
  return message || t('task.operationFailed')
}

const loadCustomerAcceptedLevel1 = async (customerId) => {
  if (!customerId) {
    customerAcceptedLevel1Ids.value = []
    return
  }
  try {
    const detail = await getCustomer(customerId)
    customerAcceptedLevel1Ids.value = detail.accepted_service_level1_ids || detail.accepted_service_level_ids || []
  } catch {
    customerAcceptedLevel1Ids.value = []
  }
}

const loadServiceLevel1Options = async () => {
  try {
    const customerId = form.customer_id
    let rows = []
    if (customerId) {
      const res = await getCustomerServiceLevel1(customerId).catch(() => [])
      rows = getArrayFromResponse(res)
      if (!rows.length) {
        const fallback = await getServiceLevel1()
        rows = getArrayFromResponse(fallback)
      }
    } else {
      const res = await getServiceLevel1()
      rows = getArrayFromResponse(res)
    }
    serviceLevel1Options.value = rows
      .map((item) => ({
        id: item.id,
        name: item.name
      }))
      .filter((i) => i.id && i.name)
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || ''
    ElMessage.error(t('task.loadServiceCatalogFailed') + (msg ? `：${msg}` : ''))
    serviceLevel1Options.value = []
  }
}

watch(
  () => form.customer_id,
  async (val, oldVal) => {
    if (val === oldVal) return
    if (suppressCustomerWatch.value) return
    const currentServices = Array.isArray(form.services) ? form.services : []
    if (currentServices.length) {
      try {
        await ElMessageBox.confirm(t('task.changeCustomerConfirm'), t('task.tip'), { type: 'warning' })
      } catch (e) {
        suppressCustomerWatch.value = true
        form.customer_id = oldVal || ''
        await nextTick()
        suppressCustomerWatch.value = false
        return
      }
      form.services = []
    }
    await loadCustomerAcceptedLevel1(val)
  }
)

const openServiceDialog = async (index = -1) => {
  if (!form.customer_id) {
    ElMessage.error(t('task.customerRequired'))
    return
  }
  if (!serviceLevel1Options.value.length) {
    await loadServiceLevel1Options()
  }
  if (!customerAcceptedLevel1Ids.value.length) {
    await loadCustomerAcceptedLevel1(form.customer_id)
  }
  if (!serviceLevel1Options.value.length) return

  serviceEditingIndex.value = index
  serviceCodeOptions.value = []
  serviceForm.service_path = []
  selectedServiceCascaderPath.value = []
  serviceStartTimeTouched.value = false
  serviceEndTimeTouched.value = false
  serviceClaimTimeTouched.value = false
  syncServiceCascaderRootOptions()

  if (index >= 0) {
    const item = form.services[index]
    const startParts = splitDateTimeParts(item.service_time_start || '')
    Object.assign(serviceForm, {
      service_path: [],
      level1_id: item.level1_id || '',
      level2_id: item.level2_id || '',
      level3_id: item.level3_id || '',
      service_code_id: item.service_code_id || '',
      service_code: item.service_code || '',
      unit_price: item.unit_price != null ? Number(item.unit_price) : null,
      duration_hours: item.duration_hours != null ? Number(item.duration_hours) : null,
      service_start_date: startParts.date,
      service_start_time: startParts.time,
      service_time_start: startParts.raw,
      service_time_end: normalizeDateTimeValue(item.service_time_end || ''),
      latest_claim_time: normalizeDateTimeValue(item.latest_claim_time || '')
    })
    const path = [serviceForm.level1_id]
    if (serviceForm.level2_id) path.push(serviceForm.level2_id)
    if (serviceForm.level3_id) path.push(serviceForm.level3_id)
    await ensureServiceCascaderPathLoaded(path)
    serviceForm.service_path = path
    selectedServiceCascaderPath.value = resolveSelectedCascaderPathNodes(path)
    if (serviceForm.level3_id) {
      await handleLevel3Change(true)
    }
    if (serviceForm.service_start_time) serviceStartTimeTouched.value = true
    serviceEndTimeTouched.value = true
    serviceClaimTimeTouched.value = true
  } else {
    Object.assign(serviceForm, {
      service_path: [],
      level1_id: '',
      level2_id: '',
      level3_id: '',
      service_code_id: '',
      service_code: '',
      unit_price: null,
      duration_hours: null,
      service_start_date: '',
      service_start_time: '',
      service_time_start: '',
      service_time_end: '',
      latest_claim_time: ''
    })
  }

  serviceDialogVisible.value = true
}

const syncServiceCascaderRootOptions = () => {
  const allow = filteredLevel1Options.value || []
  const existingMap = new Map((serviceCascaderOptions.value || []).map((n) => [String(n.value), n]))
  serviceCascaderOptions.value = allow
    .map((opt) => {
      const existed = existingMap.get(String(opt.id))
      if (existed) {
        existed.label = opt.name
        existed.nodeType = 'level1'
        existed.leaf = false
        return existed
      }
      return { value: opt.id, label: opt.name, nodeType: 'level1', leaf: false }
    })
    .filter((n) => n.value && n.label)
}

const loadCascaderChildrenForLevel1 = async (level1Id) => {
  const customerId = form.customer_id
  let res2 = []
  if (customerId) {
    res2 = await getCustomerServiceLevel2(customerId, level1Id).catch(() => [])
    if (!getArrayFromResponse(res2).length) {
      res2 = await getServiceLevel2(level1Id).catch(() => [])
    }
  } else {
    res2 = await getServiceLevel2(level1Id).catch(() => [])
  }
  const rows2 = getArrayFromResponse(res2).map((item) => ({ id: item.id, name: item.name })).filter((i) => i.id && i.name)
  if (rows2.length) {
    return rows2.map((i) => ({ value: i.id, label: i.name, nodeType: 'level2', leaf: false }))
  }
  let res3 = []
  if (customerId) {
    res3 = await getCustomerServiceLevel3(customerId, { level1_id: level1Id }).catch(() => [])
    if (!getArrayFromResponse(res3).length) {
      res3 = await getServiceLevel3({ level1_id: level1Id }).catch(() => [])
    }
  } else {
    res3 = await getServiceLevel3({ level1_id: level1Id }).catch(() => [])
  }
  const rows3 = getArrayFromResponse(res3).map((item) => ({ id: item.id, name: item.name })).filter((i) => i.id && i.name)
  return rows3.map((i) => ({ value: i.id, label: i.name, nodeType: 'level3', leaf: true }))
}

const loadCascaderChildrenForLevel2 = async (level1Id, level2Id) => {
  const customerId = form.customer_id
  const params = { level1_id: level1Id }
  if (level2Id) params.level2_id = level2Id
  let res3 = []
  if (customerId) {
    res3 = await getCustomerServiceLevel3(customerId, params).catch(() => [])
    if (!getArrayFromResponse(res3).length) {
      res3 = await getServiceLevel3(params).catch(() => [])
    }
  } else {
    res3 = await getServiceLevel3(params).catch(() => [])
  }
  const rows3 = getArrayFromResponse(res3).map((item) => ({ id: item.id, name: item.name })).filter((i) => i.id && i.name)
  return rows3.map((i) => ({ value: i.id, label: i.name, nodeType: 'level3', leaf: true }))
}

const serviceCascaderLazyLoad = async (node, resolve) => {
  if (!node) return resolve([])
  if (node.level === 1 && node?.data?.nodeType === 'level1') {
    const children = await loadCascaderChildrenForLevel1(node.value)
    return resolve(children)
  }
  if (node.level === 2 && node?.data?.nodeType === 'level2') {
    const level1Id = node?.parent?.value
    const children = await loadCascaderChildrenForLevel2(level1Id, node.value)
    return resolve(children)
  }
  return resolve([])
}

const serviceCascaderProps = {
  emitPath: true,
  expandTrigger: 'hover',
  lazy: true,
  lazyLoad: serviceCascaderLazyLoad
}

const resolveSelectedCascaderPathNodes = (values) => {
  const list = Array.isArray(values) ? values : []
  const nodes = []
  let options = serviceCascaderOptions.value || []
  for (const v of list) {
    const node = options.find((n) => String(n?.value) === String(v))
    if (!node) break
    nodes.push(node)
    options = Array.isArray(node.children) ? node.children : []
  }
  return nodes
}

const ensureServiceCascaderPathLoaded = async (path) => {
  const values = Array.isArray(path) ? path.filter(Boolean) : []
  if (!values.length) return
  syncServiceCascaderRootOptions()
  const level1Id = values[0]
  const root = serviceCascaderOptions.value.find((n) => String(n.value) === String(level1Id))
  if (!root) return
  if (!Array.isArray(root.children) || root.children.length === 0) {
    root.children = await loadCascaderChildrenForLevel1(level1Id)
  }
  if (values.length >= 3) {
    const level2Id = values[1]
    const level2Node = (root.children || []).find((n) => String(n.value) === String(level2Id) && n.nodeType === 'level2')
    if (level2Node && (!Array.isArray(level2Node.children) || level2Node.children.length === 0)) {
      level2Node.children = await loadCascaderChildrenForLevel2(level1Id, level2Id)
    }
  }
}

const handleServiceCascaderChange = async (val) => {
  serviceCodeOptions.value = []
  serviceForm.service_code_id = ''
  serviceForm.service_code = ''
  serviceForm.unit_price = null
  serviceForm.duration_hours = null

  if (!Array.isArray(val) || val.length === 0) {
    selectedServiceCascaderPath.value = []
    serviceForm.service_path = []
    serviceForm.level1_id = ''
    serviceForm.level2_id = ''
    serviceForm.level3_id = ''
    return
  }

  await ensureServiceCascaderPathLoaded(val)
  selectedServiceCascaderPath.value = resolveSelectedCascaderPathNodes(val)
  serviceForm.service_path = val

  serviceForm.level1_id = val[0] || ''
  serviceForm.level2_id = val.length === 3 ? (val[1] || '') : ''
  serviceForm.level3_id = val[val.length - 1] || ''

  if (serviceForm.level3_id) {
    if (serviceFormRef.value) {
      serviceFormRef.value.clearValidate(['service_path'])
    }
    await handleLevel3Change(false)
  }
}

const handleLevel3Change = async (keepValue = false) => {
  if (!keepValue) {
    serviceForm.service_code_id = ''
    serviceForm.service_code = ''
    serviceForm.unit_price = null
    serviceForm.duration_hours = null
  }
  serviceCodeOptions.value = []
  if (!serviceForm.level3_id) return
  const customerId = form.customer_id
  let res = []
  if (customerId) {
    res = await getCustomerServiceCodes(customerId, serviceForm.level3_id).catch(() => [])
    if (!getArrayFromResponse(res).length) {
      res = await getServiceCodes(serviceForm.level3_id).catch(() => [])
    }
  } else {
    res = await getServiceCodes(serviceForm.level3_id).catch(() => [])
  }
  const rows = getArrayFromResponse(res)
  serviceCodeOptions.value = rows
    .map((item) => {
      const code = item.code || item.service_code || item.price_code || item.priceCode || ''
      const desc = item.description || item.name || ''
      const unitPrice = parseAmount(item.unit_price ?? item.unitPrice ?? item.price ?? item.unit_price_aud ?? item.default_unit_price ?? item.unitPriceAUD)
      return {
        id: item.id,
        code,
        description: desc,
        unit_price: unitPrice,
        label: desc ? `${code} - ${desc}` : code,
        displayLabel: `${desc ? `${code} - ${desc}` : code}${unitPrice != null ? `（$${formatAmount(unitPrice)}）` : ''}`
      }
    })
    .filter((i) => i.id && i.label)

  if (!keepValue) {
    if (serviceCodeOptions.value.length >= 1) {
      serviceForm.service_code_id = serviceCodeOptions.value[0].id
      handleServiceCodeChange()
    }
  } else if (serviceForm.service_code_id) {
    handleServiceCodeChange()
  }
}

const getServicePrefStorageKey = () => {
  const token = localStorage.getItem('token') || ''
  const suffix = token ? token.slice(-16) : 'guest'
  return `task_service_last_values:${suffix}`
}

const readServicePrefStore = () => {
  try {
    const raw = localStorage.getItem(getServicePrefStorageKey())
    if (!raw) return {}
    const obj = JSON.parse(raw)
    return obj && typeof obj === 'object' ? obj : {}
  } catch {
    return {}
  }
}

const writeServicePrefStore = (store) => {
  try {
    localStorage.setItem(getServicePrefStorageKey(), JSON.stringify(store || {}))
  } catch {}
}

const buildServicePrefKey = ({ customerId, level3Id, serviceCodeId, serviceCode }) => {
  const cid = normalizeString(customerId)
  const l3 = normalizeString(level3Id)
  const scid = normalizeString(serviceCodeId)
  const sc = normalizeString(serviceCode)
  return `${cid}::${l3}::${scid || sc}`
}

const applyLastServicePrefToForm = () => {
  const customerId = form.customer_id
  const key = buildServicePrefKey({
    customerId,
    level3Id: serviceForm.level3_id,
    serviceCodeId: serviceForm.service_code_id,
    serviceCode: serviceForm.service_code
  })
  const store = readServicePrefStore()
  const saved = store[key]
  if (!saved || typeof saved !== 'object') return
  if (saved.unit_price != null && !isNaN(Number(saved.unit_price))) {
    serviceForm.unit_price = Number(saved.unit_price)
  }
  if (saved.duration_hours != null && !isNaN(Number(saved.duration_hours))) {
    serviceForm.duration_hours = Number(saved.duration_hours)
  }
}

const recordLastServicePrefsFromTaskForm = () => {
  const customerId = form.customer_id
  if (!customerId) return
  const list = Array.isArray(form.services) ? form.services : []
  if (!list.length) return
  const store = readServicePrefStore()
  for (const s of list) {
    const unit = s?.unit_price
    const dur = s?.duration_hours
    if (unit == null || dur == null) continue
    if (isNaN(Number(unit)) || isNaN(Number(dur))) continue
    const key = buildServicePrefKey({
      customerId,
      level3Id: s?.level3_id,
      serviceCodeId: s?.service_code_id,
      serviceCode: s?.service_code
    })
    store[key] = { unit_price: Number(unit), duration_hours: Number(dur), updated_at: Date.now() }
  }
  writeServicePrefStore(store)
}

const handleServiceCodeChange = () => {
  const matched = serviceCodeOptions.value.find((i) => String(i.id) === String(serviceForm.service_code_id))
  if (!matched) return
  serviceForm.service_code = matched.code || matched.label
  if (matched.unit_price != null) {
    serviceForm.unit_price = matched.unit_price
  }
  applyLastServicePrefToForm()
}

const saveServiceItem = async () => {
  if (!serviceFormRef.value) return
  applyDerivedServiceTimes()
  await serviceFormRef.value.validate(async (valid) => {
    if (!valid) return
    if (serviceForm.service_time_start && serviceForm.service_time_end) {
      const start = new Date(serviceForm.service_time_start.replace(' ', 'T'))
      const end = new Date(serviceForm.service_time_end.replace(' ', 'T'))
      if (end <= start) {
        ElMessage.error(t('task.endAfterStart'))
        return
      }
    }

    const path = selectedServiceCascaderPath.value || []
    const level1 = path.find((n) => n?.nodeType === 'level1') || serviceLevel1Options.value.find((i) => String(i.id) === String(serviceForm.level1_id))
    const level2 = path.find((n) => n?.nodeType === 'level2')
    const level3 = path.find((n) => n?.nodeType === 'level3')
    const existingId = serviceEditingIndex.value >= 0 ? (form.services?.[serviceEditingIndex.value]?.id || '') : ''
    const payload = {
      id: existingId,
      level1_id: serviceForm.level1_id,
      level1_name: level1?.label || level1?.name || '',
      level2_id: serviceForm.level2_id || null,
      level2_name: level2?.label || '',
      level3_id: serviceForm.level3_id,
      level3_name: level3?.label || '',
      service_code_id: serviceForm.service_code_id,
      service_code: serviceForm.service_code,
      unit_price: serviceForm.unit_price != null ? Number(serviceForm.unit_price) : null,
      duration_hours: serviceForm.duration_hours != null ? Number(serviceForm.duration_hours) : null,
      total_price: serviceTotalPrice.value,
      service_time_start: serviceForm.service_time_start,
      service_time_end: serviceForm.service_time_end,
      latest_claim_time: serviceForm.latest_claim_time
    }

    if (serviceEditingIndex.value >= 0) {
      form.services.splice(serviceEditingIndex.value, 1, payload)
    } else {
      form.services.push(payload)
    }
    serviceDialogVisible.value = false
  })
}

const removeServiceItem = async (index) => {
  try {
    await ElMessageBox.confirm(t('task.removeServiceConfirm'), t('task.tip'), { type: 'warning' })
    form.services.splice(index, 1)
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') throw e
  }
}

const buildDerivedTimes = () => {
  const list = Array.isArray(form.services) ? form.services : []
  const starts = list.map((s) => s.service_time_start).filter(Boolean).sort()
  const ends = list.map((s) => s.service_time_end).filter(Boolean).sort()
  const claims = list.map((s) => s.latest_claim_time).filter(Boolean).sort()
  return {
    service_start_time: starts.length ? starts[0] : null,
    service_end_time: ends.length ? ends[ends.length - 1] : null,
    latest_claim_time: claims.length ? claims[0] : null
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (!form.services.length) {
          ElMessage.error(t('task.serviceRequired'))
          return
        }
        if (!editingTaskId.value && form.repeat_rule) {
          if (!form.repeat_months) {
            ElMessage.error(t('task.repeatMonthsRequired'))
            return
          }
        }
        const derived = buildDerivedTimes()
        const validateServiceLine = (s) => {
          const code = normalizeString(s?.service_code || '')
          const hours = Number(s?.duration_hours)
          if (!code) return { ok: false, message: t('task.selectServiceCode') }
          if (!Number.isFinite(hours) || hours <= 0) return { ok: false, message: t('task.durationRequired') }
          return { ok: true, code, hours }
        }
        const buildServicePayload = (s) => {
          const v = validateServiceLine(s)
          if (!v.ok) throw new Error(v.message)
          const unit = Number(s?.unit_price)
          const payload = {
            service_code: v.code,
            duration_hours: v.hours,
            unit_price_override: Number.isFinite(unit) && unit > 0 ? unit : null
          }
          if (s.level1_id) payload.level1_id = s.level1_id
          if (s.level2_id) payload.level2_id = s.level2_id
          if (s.level3_id) payload.level3_id = s.level3_id
          if (s.service_time_start) payload.service_time_start = s.service_time_start
          if (s.service_time_end) payload.service_time_end = s.service_time_end
          return payload
        }

        const normalizedServices = (Array.isArray(form.services) ? form.services : []).map(buildServicePayload)

        const taskPayload = {
          title: form.title,
          description: form.description,
          customer_id: form.customer_id,
          assigned_employee_id: form.assigned_employee_id || null,
          questionnaire_id: form.questionnaire_id || null,
          incident_template_id: form.incident_template_id || null,
          task_record_template_id: form.task_record_template_id || null,
          questionnaires: (form.questionnaires || [])
            .filter((q) => q.questionnaire_id)
            .map((q, idx) => ({
              questionnaire_id: q.questionnaire_id,
              is_required: q.is_required,
              order_index: idx
            })),
          service_start_time: derived.service_start_time,
          service_end_time: derived.service_end_time,
          latest_claim_time: derived.latest_claim_time
        }

        if (editingTaskId.value) {
          let updatedViaTaskApi = false
          try {
            await updateTask(editingTaskId.value, taskPayload)
            updatedViaTaskApi = true
          } catch (e) {
            if (e?.response?.status === 422) {
              await updateTask(editingTaskId.value, { ...taskPayload, services: normalizedServices })
              updatedViaTaskApi = false
            } else {
              throw e
            }
          }

          const currentList = Array.isArray(form.services) ? form.services : []
          const currentIds = new Set(currentList.map((s) => s?.id).filter(Boolean))
          const deletedIds = (originalServiceIds.value || []).filter((id) => !currentIds.has(id))
          const currentFingerprint = buildServicesFingerprint(currentList)
          const shouldSyncServices = currentFingerprint !== originalServicesFingerprint.value || deletedIds.length > 0

          if (updatedViaTaskApi && shouldSyncServices) {
            const ops = []
            currentList.forEach((s) => {
              const svcPayload = buildServicePayload(s)
              if (s?.id) ops.push(updateTaskService(editingTaskId.value, s.id, svcPayload))
              else ops.push(addTaskService(editingTaskId.value, svcPayload))
            })
            deletedIds.forEach((id) => {
              ops.push(deleteTaskService(editingTaskId.value, id))
            })
            if (ops.length) await Promise.all(ops)
            originalServiceIds.value = Array.from(currentIds)
            originalServicesFingerprint.value = currentFingerprint
          }

          ElMessage.success(t('task.updateSuccess'))
          await loadTasks()
        } else {
          const repeatPayload = form.repeat_rule
            ? { repeat_rule: form.repeat_rule, repeat_months: form.repeat_months }
            : {}
          const res = await createTask({ ...taskPayload, ...repeatPayload, services: normalizedServices })
          const createdId = res?.id ?? res?.task_id ?? res?.taskId ?? res?.data?.id ?? null
          if (createdId) {
            try {
              const existing = await getTaskServices(createdId)
              const rows = getArrayFromResponse(existing)
              if (rows.length < normalizedServices.length) {
                await Promise.all(normalizedServices.map((p) => addTaskService(createdId, p)))
              }
            } catch {}
          }
          recordLastServicePrefsFromTaskForm()
          ElMessage.success(t('task.createSuccess'))
        }
        dialogVisible.value = false
        loadTasks()
      } catch (error) {
        ElMessage.error(getErrorMessage(error))
      }
    }
  })
}

onMounted(() => {
  loadTasks()
  loadSearchCandidates()
  loadCustomers()
  loadEmployees()
  loadServiceLevel1Options()
  loadQuestionnaires()
  loadIncidentTemplates()
  loadTaskRecordTemplates()
})
</script>

<style scoped>
.task-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}

.pager-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.task-form .el-form-item__label {
  white-space: nowrap;
}

.task-total-price {
  font-weight: 600;
  font-size: 18px;
}

.service-code-radio {
  width: 100%;
}

.clickable-with-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.row-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
}

.duplicate-start-time {
  color: var(--el-color-danger);
  font-weight: 600;
}

.duplicate-tip__actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 8px;
}

.task-calendar :deep(.el-calendar-table .el-calendar-day) {
  padding: 6px;
}

.calendar-day {
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.calendar-day__num {
  font-size: 18px;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 6px;
}

.calendar-day--has-tasks .calendar-day__num {
  color: var(--el-color-danger);
  font-weight: 700;
  background: rgba(245, 108, 108, 0.12);
}

.calendar-day__count {
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  line-height: 18px;
  color: #fff;
  background: var(--el-color-danger);
}

.calendar-popover__count {
  margin-left: 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.calendar-popover__title {
  font-weight: 600;
  margin-bottom: 8px;
}

.calendar-popover__list {
  max-height: 360px;
  overflow: auto;
  padding-right: 6px;
}

.calendar-popover__pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.calendar-task {
  padding: 8px 10px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
}

.calendar-task__title {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
}

.calendar-task__status {
  flex: 0 0 auto;
}

.calendar-task__meta {
  margin-top: 6px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.calendar-task__meta-item {
  display: inline-flex;
  gap: 6px;
}

.calendar-popover__item {
  line-height: 1.8;
  margin-top: 8px;
}

</style>
