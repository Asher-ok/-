<template>
  <div class="qualification-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('qualifications.title') }}</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" @tab-change="loadQualifications">
        <el-tab-pane :label="$t('qualifications.trainingRecords')" name="training">
          <TrainingRecordManager
            :employees="employees"
            :display-mode="'dropdown'"
            :show-employee-select="true"
            :show-status-columns="true"
            :show-employee-columns="true"
            @refresh="loadEmployees"
          />
        </el-tab-pane>
        <el-tab-pane :label="$t('qualifications.expiring')" name="expiring">
          <el-space :size="12" style="margin-bottom: 16px">
            <span>{{ $t('qualifications.reminderDays') }}</span>
            <el-input-number v-model="reminderDays" :min="1" :max="3650" />
            <el-button type="primary" :loading="reminderSettingLoading" @click="saveReminderSetting">{{ $t('common.save') }}</el-button>
          </el-space>
          <el-table
            :data="sortedExpiringTrainingRecords"
            v-loading="loading"
            stripe
            table-layout="auto"
            style="width: 100%"
            :default-sort="{ prop: 'expiry_date', order: 'descending' }"
            @sort-change="handleExpiringSortChange"
          >
            <el-table-column :label="$t('qualifications.employeeName')" width="140">
              <template #default="{ row }">
                <span>{{ row.employee_name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.employeeNumber')" width="140">
              <template #default="{ row }">
                <span>{{ row.employee_number || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.trainingName')" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span>{{ row.name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.trainingCategory')" width="140">
              <template #default="{ row }">
                <span>{{ getCategoryName(row.category) || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="completed_date" column-key="completed_date" :label="$t('qualifications.trainingDate')" width="160" sortable="custom">
              <template #default="{ row }">
                <span>{{ formatDate(row.completed_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="expiry_date" column-key="expiry_date" :label="$t('qualifications.expiryDate')" width="160" sortable="custom">
              <template #default="{ row }">
                <span>{{ formatDate(row.expiry_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.daysUntilExpiry')" width="140">
              <template #default="{ row }">
                <el-tag :type="getDaysUntilExpiryTagType(row.days_until_expiry)" size="small">
                  {{ row.days_until_expiry < 0 ? $t('qualifications.expired') : `${row.days_until_expiry}${$t('qualifications.days')}` }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.reminderStatus')" width="160">
              <template #default="{ row }">
                <el-tag :type="getReminderStatusTag(row.reminder_status)">
                  {{ getReminderStatusText(row.reminder_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.certificate')" width="120">
              <template #default="{ row }">
                <el-link v-if="row.certificate_url" type="primary" @click="openTrainingCertificatePreview(row)">{{ $t('common.view') }}</el-link>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.operations')" width="110" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="editTrainingRecord(row)">{{ $t('common.edit') }}</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && sortedExpiringTrainingRecords.length === 0" :description="$t('qualifications.noExpiringRecords')" />
        </el-tab-pane>
        <el-tab-pane :label="$t('qualifications.expired')" name="expired">
          <el-table
            :data="sortedExpiredTrainingRecords"
            v-loading="loading"
            stripe
            table-layout="auto"
            style="width: 100%"
            :default-sort="{ prop: 'expiry_date', order: 'descending' }"
            @sort-change="handleExpiredSortChange"
          >
            <el-table-column :label="$t('qualifications.employeeName')" width="140">
              <template #default="{ row }">
                <span>{{ row.employee_name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.employeeNumber')" width="140">
              <template #default="{ row }">
                <span>{{ row.employee_number || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.trainingName')" min-width="120" show-overflow-tooltip>
              <template #default="{ row }">
                <span>{{ row.name || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.trainingCategory')" width="140">
              <template #default="{ row }">
                <span>{{ getCategoryName(row.category) || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="completed_date" column-key="completed_date" :label="$t('qualifications.trainingDate')" width="160" sortable="custom">
              <template #default="{ row }">
                <span>{{ formatDate(row.completed_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="expiry_date" column-key="expiry_date" :label="$t('qualifications.expiryDate')" width="160" sortable="custom">
              <template #default="{ row }">
                <span>{{ formatDate(row.expiry_date) }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.daysUntilExpiry')" width="140">
              <template #default="{ row }">
                <el-tag :type="getDaysUntilExpiryTagType(row.days_until_expiry)" size="small">
                  {{ row.days_until_expiry < 0 ? `${$t('qualifications.expired')}${Math.abs(row.days_until_expiry)}${$t('qualifications.days')}` : `${row.days_until_expiry}${$t('qualifications.days')}` }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.reminderStatus')" width="160">
              <template #default="{ row }">
                <el-tag :type="getReminderStatusTag(row.reminder_status)">
                  {{ getReminderStatusText(row.reminder_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.certificate')" width="120">
              <template #default="{ row }">
                <el-link v-if="row.certificate_url" type="primary" @click="openTrainingCertificatePreview(row)">{{ $t('common.view') }}</el-link>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('qualifications.operations')" width="110" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click="editTrainingRecord(row)">{{ $t('common.edit') }}</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && sortedExpiredTrainingRecords.length === 0" :description="$t('qualifications.noExpiredRecords')" />
        </el-tab-pane>
        <el-tab-pane :label="$t('qualifications.bulkUpload')" name="bulk-upload">
          <div class="bulk-upload-section">
            <el-form :model="bulkUploadForm" label-width="150px">
              <el-form-item :label="$t('qualifications.selectDocumentType')">
                <el-select v-model="bulkUploadForm.documentType" :placeholder="$t('qualifications.selectDocumentTypePlaceholder')" style="width: 100%">
                  <el-option :label="$t('qualifications.documentTypes.checklist')" value="checklist" />
                  <el-option :label="$t('qualifications.documentTypes.code')" value="code" />
                  <el-option :label="$t('qualifications.documentTypes.tracker')" value="tracker" />
                  <el-option :label="$t('qualifications.documentTypes.handbook')" value="handbook" />
                  <el-option :label="$t('qualifications.documentTypes.onboarding')" value="onboarding" />
                </el-select>
              </el-form-item>
              <el-form-item :label="$t('qualifications.uploadFile')">
                <el-upload
                  ref="bulkUploadRef"
                  :auto-upload="false"
                  :on-change="handleBulkUploadChange"
                  :file-list="bulkUploadFileList"
                  :limit="1"
                  drag
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text" v-html="$t('qualifications.dragTip')">
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      {{ $t('qualifications.fileTip') }}
                    </div>
                  </template>
                </el-upload>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="bulkUploadLoading" @click="handleBulkUpload">
                  {{ $t('common.upload') }}
                </el-button>
                <el-button @click="resetBulkUploadForm">{{ $t('common.cancel') }}</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    <el-dialog v-model="previewDialogVisible" :title="$t('qualifications.previewTitle')" width="900px" @closed="clearPreview">
      <div class="preview-body" v-loading="previewLoading">
        <img v-if="previewUrl" :src="previewUrl" :alt="$t('qualifications.previewTitle')" class="preview-image" />
        <div v-else class="preview-empty">{{ $t('qualifications.noCertificate') }}</div>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">{{ $t('common.cancel') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({
  name: 'Qualifications'
})
import { ref, onMounted, reactive, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getEmployees, getExpiringTrainingRecords, getExpiredTrainingRecords, getTrainingRecordReminderSettings, updateTrainingRecordReminderSettings, bulkUploadEmployeeDocument } from '@/api/employees'
import { markUpdatesRead } from '@/api/updates'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import TrainingRecordManager from '@/components/TrainingRecordManager.vue'
import { formatDate } from '@/utils/formatters'
import api from '@/api'

const router = useRouter()
const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))

const expiringTrainingRecords = ref([])
const expiredTrainingRecords = ref([])
const loading = ref(false)
const activeTab = ref('training')
const employees = ref([])
const previewDialogVisible = ref(false)
const previewUrl = ref('')
const previewLoading = ref(false)
const reminderDays = ref(90)
const reminderSettingLoading = ref(false)
const expiringSortState = reactive({
  prop: 'expiry_date',
  order: 'descending'
})
const expiredSortState = reactive({
  prop: 'expiry_date',
  order: 'descending'
})

// 批量上传相关
const bulkUploadForm = ref({
  documentType: ''
})
const bulkUploadFileList = ref([])
const bulkUploadRef = ref(null)
const bulkUploadLoading = ref(false)

const toTime = (value) => {
  const ms = new Date(value || '').getTime()
  return Number.isFinite(ms) ? ms : 0
}

const sortTrainingRecords = (rows, sortState) => {
  const list = Array.isArray(rows) ? [...rows] : []
  const { prop, order } = sortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'completed_date' || prop === 'expiry_date') {
    return list.sort((a, b) => (toTime(a?.[prop]) - toTime(b?.[prop])) * dir)
  }
  return list
}

const sortedExpiringTrainingRecords = computed(() => sortTrainingRecords(expiringTrainingRecords.value, expiringSortState))
const sortedExpiredTrainingRecords = computed(() => sortTrainingRecords(expiredTrainingRecords.value, expiredSortState))

const handleExpiringSortChange = ({ prop, order }) => {
  expiringSortState.prop = prop || ''
  expiringSortState.order = order
}

const handleExpiredSortChange = ({ prop, order }) => {
  expiredSortState.prop = prop || ''
  expiredSortState.order = order
}

const loadQualifications = async () => {
  loading.value = true
  try {
    if (activeTab.value === 'expiring') {
      const result = await getExpiringTrainingRecords(reminderDays.value)
      expiringTrainingRecords.value = result || []
    } else if (activeTab.value === 'expired') {
      const result = await getExpiredTrainingRecords()
      expiredTrainingRecords.value = result || []
    } else if (activeTab.value === 'training') {
      // 培训记录由组件自己管理
    }
  } catch (error) {
    ElMessage.error(t('qualifications.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const loadEmployees = async () => {
  try {
    employees.value = await getEmployees()
  } catch (error) {
    ElMessage.error(t('qualifications.messages.loadEmployeesFailed'))
  }
}

const clearPreview = () => {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = ''
}

const loadReminderSetting = async () => {
  try {
    const result = await getTrainingRecordReminderSettings()
    if (result?.days) {
      reminderDays.value = result.days
    }
  } catch (error) {
    ElMessage.error(t('qualifications.messages.loadReminderFailed'))
  }
}

const saveReminderSetting = async () => {
  if (!reminderDays.value || reminderDays.value <= 0) {
    ElMessage.error(t('qualifications.messages.reminderDaysRequired'))
    return
  }
  reminderSettingLoading.value = true
  try {
    await updateTrainingRecordReminderSettings(reminderDays.value)
    ElMessage.success(t('qualifications.messages.saveSuccess'))
    if (activeTab.value === 'expiring') {
      await loadQualifications()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('qualifications.messages.saveFailed'))
  } finally {
    reminderSettingLoading.value = false
  }
}

// 培训记录相关函数
const getCategoryName = (category) => {
  const categoryMap = {
    'first-aid': 'First Aid',
    'manual-handling': 'Manual Handling',
    'certificate': 'Certificate'
  }
  return categoryMap[category] || category
}

const getReminderStatusText = (status) => {
  const statusMap = {
    '3_months': t('qualifications.reminderStatusText.threeMonths'),
    '1_month': t('qualifications.reminderStatusText.oneMonth'),
    '1_week': t('qualifications.reminderStatusText.oneWeek'),
    'expired': t('qualifications.reminderStatusText.expired'),
    'normal': t('qualifications.reminderStatusText.normal')
  }
  return statusMap[status] || status
}

const getReminderStatusTag = (status) => {
  const tagMap = {
    '3_months': 'warning',
    '1_month': 'warning',
    '1_week': 'danger',
    'expired': 'danger',
    'normal': 'info'
  }
  return tagMap[status] || 'info'
}

const getDaysUntilExpiryTagType = (days) => {
  if (days < 0) return 'danger'
  if (days <= 7) return 'warning'
  if (days <= 30) return 'warning'
  return 'success'
}

const openTrainingCertificatePreview = async (row) => {
  if (!row.certificate_url) {
    ElMessage.warning(t('qualifications.messages.noCertificate'))
    return
  }
  previewDialogVisible.value = true
  previewLoading.value = true
  
  // 清除旧的blob URL缓存
  clearPreview()
  
  try {
    const normalizeUrl = (rawUrl) => {
      if (!rawUrl) return ''
      if (/^https?:\/\//i.test(rawUrl)) return rawUrl
      return rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`
    }

    const baseUrl = (api?.defaults?.baseURL || '').replace(/\/$/, '')
    let certificateUrl = normalizeUrl(row.certificate_url)
    if (certificateUrl.toLowerCase().includes('/uploads/')) {
      certificateUrl = `${baseUrl}/houtai/employees/${row.employee_id}/training-records/${row.id}/certificate`
    }
    certificateUrl += `?_t=${Date.now()}`
    
    const token = localStorage.getItem('token')
    const response = await fetch(certificateUrl, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      },
      cache: 'no-store' // 禁用缓存
    })
    if (!response.ok) {
      throw new Error(t('qualifications.messages.certificateLoadFailed'))
    }
    const blob = await response.blob()
    previewUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    ElMessage.error(t('qualifications.messages.certificateLoadFailed'))
  } finally {
    previewLoading.value = false
  }
}

const editTrainingRecord = (row) => {
  // 跳转到员工详情页的培训记录部分
  router.push({
    path: `/employees/${row.employee_id}`,
    query: {
      tab: 'qualifications',
      qualificationTab: 'training',
      recordId: row.id // 传递培训记录ID，以便后续可以定位到具体记录
    }
  })
}

// 批量上传相关方法
const handleBulkUploadChange = (file, files) => {
  bulkUploadFileList.value = files
}

const handleBulkUpload = async () => {
  if (!bulkUploadForm.value.documentType) {
    ElMessage.warning(t('qualifications.messages.selectDocumentType'))
    return
  }
  
  if (bulkUploadFileList.value.length === 0) {
    ElMessage.warning(t('qualifications.messages.selectFile'))
    return
  }
  
  const file = bulkUploadFileList.value[0].raw || bulkUploadFileList.value[0]
  if (!file) {
    ElMessage.warning(t('qualifications.messages.selectFile'))
    return
  }
  
  bulkUploadLoading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', bulkUploadForm.value.documentType)
    
    await bulkUploadEmployeeDocument(formData)
    ElMessage.success(t('qualifications.uploadSuccess'))
    resetBulkUploadForm()
  } catch (error) {
    console.error('批量上传失败:', error)
    ElMessage.error(t('qualifications.uploadFailed') + ': ' + (error.response?.data?.detail || error.message || t('common.noData')))
  } finally {
    bulkUploadLoading.value = false
  }
}

const resetBulkUploadForm = () => {
  bulkUploadForm.value = {
    documentType: ''
  }
  bulkUploadFileList.value = []
  if (bulkUploadRef.value) {
    bulkUploadRef.value.clearFiles()
  }
}


onMounted(() => {
  markUpdatesRead('qualification').catch(() => {})
  loadEmployees()
  loadQualifications()
  loadReminderSetting()
})
</script>

<style scoped>
.qualification-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}


.preview-body {
  min-height: 520px;
}

.preview-image {
  width: 100%;
  max-height: 520px;
  object-fit: contain;
}

.preview-empty {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.bulk-upload-section {
  padding: 20px;
}
</style>
