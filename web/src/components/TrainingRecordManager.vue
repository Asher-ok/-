<template>
  <div class="training-record-manager">
    <!-- 分类选择区域 -->
    <div v-if="displayMode === 'tabs'" class="category-selector">
      <el-menu
        :default-active="activeCategory"
        @select="handleCategorySelect"
        mode="horizontal"
        class="category-menu"
      >
        <el-menu-item index="certificate">Certificate</el-menu-item>
        <el-menu-item index="first-aid">First Aid</el-menu-item>
        <el-menu-item index="manual-handling">Manual Handling</el-menu-item>
      </el-menu>
    </div>
    
    <!-- 内容区域 -->
    <div class="content-area">
      <div class="section-header">
        <div v-if="displayMode !== 'tabs'" class="filter-bar">
          <el-select v-model="categoryFilter" :placeholder="$t('training.selectCategory')" clearable style="width: 180px" @change="handleCategoryFilterChange">
            <el-option label="Certificate" value="certificate" />
            <el-option label="First Aid" value="first-aid" />
            <el-option label="Manual Handling" value="manual-handling" />
            <el-option :label="$t('training.all')" value="" />
          </el-select>
          <el-input 
            v-if="showEmployeeColumns" 
            v-model="searchKeyword" 
            :placeholder="$t('training.searchPlaceholder')" 
            clearable 
            style="width: 260px" 
            @clear="handleSearch"
          />
          <el-button v-if="showEmployeeColumns" type="primary" @click="handleSearch">{{ $t('training.searchButton') }}</el-button>
        </div>
        <h3 v-else-if="showTitle" class="section-title">
          {{ getCategoryName(activeCategory) }}{{ $t('training.trainingRecord') }}
        </h3>
        <h3 v-else-if="showTitle" class="section-title">{{ $t('training.trainingRecord') }}</h3>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          {{ $t('training.addTrainingRecord') }}
        </el-button>
      </div>
      
      <el-table 
        :data="filteredRecords" 
        v-loading="loading" 
        :row-class-name="getRowClassName"
        table-layout="auto"
        style="width: 100%"
        :default-sort="{ prop: 'completed_date', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column v-if="showEmployeeColumns" :label="$t('training.employeeName')" width="120">
          <template #default="{ row }">
            <span>{{ row.employee_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="showEmployeeColumns" :label="$t('training.employeeNumber')" width="120">
          <template #default="{ row }">
            <span>{{ row.employee_number || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('training.trainingName')" min-width="240" show-overflow-tooltip />
        <el-table-column v-if="showStatusColumns" :label="$t('training.passed')" width="140">
          <template #default="{ row }">
            <el-dropdown 
              v-if="row.status === 'pending' && row.created_by === 'employee'"
              @command="(command) => handleStatusAction(command, row)"
              trigger="click"
            >
              <el-tag 
                :type="getTrainingStatusTag(row.status, row.created_by)"
                :class="{ 'status-tag-clickable': row.status === 'pending' && row.created_by === 'employee' }"
              >
                {{ getTrainingStatusText(row.status) }}
              </el-tag>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="approve">{{ $t('training.approve') }}</el-dropdown-item>
                  <el-dropdown-item command="reject">{{ $t('training.reject') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-tag v-else :type="getTrainingStatusTag(row.status, row.created_by)">{{ getTrainingStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="showStatusColumns" :label="$t('training.certificateIssued')" width="100">
          <template #default="{ row }">
            <el-tag 
              :type="row.has_certificate ? 'success' : 'info'"
              :class="{ 'certificate-tag-clickable': row.has_certificate }"
              @click="row.has_certificate && handleViewCertificate(row)"
            >
              {{ row.has_certificate ? $t('common.yes') : $t('common.no') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('training.trainingCategory')" width="120">
          <template #default="{ row }">
            <span>{{ getCategoryName(row.category) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="completed_date" column-key="completed_date" :label="displayMode === 'tabs' ? $t('training.completionDate') : $t('training.trainingDate')" width="140" sortable="custom">
          <template #default="{ row }">
            {{ formatDate(row.completed_date) }}
          </template>
        </el-table-column>
        <el-table-column v-if="displayMode === 'tabs'" prop="score" :label="$t('training.score')" width="100" />
        <el-table-column prop="training_institution" :label="$t('training.trainingInstitution')" min-width="180" show-overflow-tooltip />
        <el-table-column prop="notes" :label="$t('training.notes')" min-width="260" show-overflow-tooltip />
        <el-table-column :label="$t('training.operations')" width="160" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
          <template #default="{ row }">
            <div class="action-buttons action-buttons--scroll">
              <div class="action-buttons-inner">
                <el-button type="primary" size="small" @click="handleEdit(row)">{{ $t('training.edit') }}</el-button>
                <el-button type="danger" size="small" @click="handleDelete(row)">{{ $t('training.delete') }}</el-button>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && filteredRecords.length === 0" :description="getEmptyDescription()" />
    </div>
    
    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="520px" @closed="handleDialogClosed">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item v-if="showEmployeeSelect" :label="$t('training.selectEmployee')" prop="employee_id">
          <el-select v-model="form.employee_id" :placeholder="$t('training.selectEmployee')" style="width: 100%" :disabled="isEditMode">
            <el-option v-for="employee in employees" :key="employee.id" :label="employee.name" :value="employee.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('training.selectCategory')" prop="category">
          <el-select v-model="form.category" :placeholder="$t('training.selectCategory')" style="width: 100%">
            <el-option label="Certificate" value="certificate" />
            <el-option label="First Aid" value="first-aid" />
            <el-option label="Manual Handling" value="manual-handling" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('training.trainingName')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="$t('training.trainingDate')" prop="completed_date">
          <el-date-picker v-model="form.completed_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
        <el-form-item v-if="displayMode === 'tabs'" :label="$t('training.score')">
          <el-input v-model="form.score" />
        </el-form-item>
        <el-form-item :label="$t('training.trainingInstitution')">
          <el-input v-model="form.training_institution" />
        </el-form-item>
        <el-form-item :label="$t('training.passed')" prop="status">
          <el-select v-model="form.status" :placeholder="$t('training.selectStatus')" style="width: 100%">
            <el-option :label="$t('training.pending')" value="pending" />
            <el-option :label="$t('training.inProgress')" value="in_progress" />
            <el-option :label="$t('training.completed')" value="completed" />
            <el-option :label="$t('training.rejected')" value="rejected" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('training.certificateIssued')">
          <el-switch v-model="form.has_certificate" />
        </el-form-item>
        <el-form-item v-if="form.has_certificate" :label="$t('training.certificateNumber')">
          <el-input v-model="form.certificate_number" :placeholder="$t('training.inputCertificateNumber')" />
        </el-form-item>
        <el-form-item v-if="form.has_certificate" :label="$t('training.issueDate')">
          <el-date-picker v-model="form.certificate_obtained_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" :placeholder="$t('training.selectIssueDate')" />
        </el-form-item>
        <el-form-item v-if="form.has_certificate" :label="$t('training.expiryDate')">
          <el-date-picker v-model="form.certificate_expiry_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" :placeholder="$t('training.selectExpiryDate')" />
        </el-form-item>
        <el-form-item v-if="form.has_certificate" :label="$t('training.certificateFile')">
          <!-- 编辑模式：显示当前证书 -->
          <div v-if="isEditMode && editingRecord?.certificate_url && !certificateFile && !certificateDeleted" class="certificate-preview-edit">
            <div class="certificate-image-wrapper" v-loading="editingCertificateLoading">
              <iframe
                v-if="editingCertificatePreviewUrl && isPreviewPdf(editingCertificatePreviewUrl, editingCertificatePreviewMime)"
                :src="editingCertificatePreviewUrl"
                class="certificate-preview-iframe"
              ></iframe>
              <img
                v-else-if="editingCertificatePreviewUrl"
                :src="editingCertificatePreviewUrl"
                alt="证书图片"
                class="certificate-preview-img"
                @error="handleImageError"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                size="small"
                class="certificate-delete-btn"
                @click="handleDeleteCertificate"
                :title="$t('training.delete')"
              />
            </div>
            <div class="certificate-actions">
              <el-button type="primary" @click="triggerFileInput">{{ $t('training.reupload') }}</el-button>
            </div>
          </div>
          <!-- 编辑模式：已删除证书，显示上传 -->
          <div v-else-if="isEditMode && certificateDeleted" class="certificate-deleted">
            <el-alert type="warning" :closable="false" show-icon>
              <template #default>
                <span>{{ $t('training.certificateDeleted') }}</span>
                <el-button type="primary" size="small" @click="certificateDeleted = false" style="margin-left: 10px">{{ $t('training.cancelDelete') }}</el-button>
              </template>
            </el-alert>
          </div>
          <!-- 上传组件 -->
          <div v-if="!isEditMode || certificateFile || certificateDeleted">
            <el-upload
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :file-list="fileList"
              :ref="uploadRef"
            >
              <el-button type="primary">{{ $t('training.selectFile') }}</el-button>
              <template #tip>
                <div class="el-upload__tip">
                  {{ $t('training.supportFormats') }}
                </div>
              </template>
            </el-upload>
          </div>
          <!-- 编辑模式：无证书文件 -->
          <div v-else-if="isEditMode && !editingRecord?.certificate_url" class="certificate-empty-edit">
            <span class="text-gray-500">{{ $t('training.noCertificateFile') }}</span>
            <el-button type="primary" @click="triggerFileInput" style="margin-left: 10px">{{ $t('training.uploadCertificate') }}</el-button>
          </div>
        </el-form-item>
        <el-form-item :label="$t('training.notes')">
          <el-input v-model="form.notes" type="textarea" rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('training.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ $t('training.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- 查看证书对话框 -->
    <el-dialog v-model="certificateDialogVisible" :title="$t('training.viewCertificateTitle')" width="900px" @closed="clearCertificatePreview">
      <div v-if="viewingCertificate" class="certificate-view">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('training.certificateNumber')">{{ viewingCertificate.certificate_number || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('training.issueDate')">{{ formatDate(viewingCertificate.certificate_obtained_date || viewingCertificate.completed_date) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('training.expiryDate')" :span="2">
            {{ viewingCertificate.certificate_expiry_date ? formatDate(viewingCertificate.certificate_expiry_date) : $t('training.permanent') }}
          </el-descriptions-item>
        </el-descriptions>
        <div class="certificate-image-container" v-loading="certificatePreviewLoading">
          <iframe
            v-if="certificatePreviewUrl && isPreviewPdf(certificatePreviewUrl, certificatePreviewMime)"
            :src="certificatePreviewUrl"
            class="certificate-iframe"
          ></iframe>
          <img
            v-else-if="certificatePreviewUrl"
            :src="certificatePreviewUrl"
            alt="证书图片"
            class="certificate-image"
            @error="handleCertificateImageError"
          />
          <div v-else-if="viewingCertificate.certificate_url && certificatePreviewLoading" class="certificate-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>{{ $t('training.loading') }}</span>
          </div>
          <div v-else-if="viewingCertificate.certificate_url && !certificatePreviewUrl" class="certificate-error">
            <el-alert type="error" :closable="false" show-icon>
              <template #default>
                <span>{{ $t('training.certificateImageLoadFailed') }}</span>
                <el-button type="primary" size="small" @click="retryLoadCertificate" style="margin-left: 10px">{{ $t('training.retry') }}</el-button>
              </template>
            </el-alert>
          </div>
          <div v-else class="certificate-empty">
            <el-empty :description="$t('training.noCertificateImage')" />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="certificateDialogVisible = false">{{ $t('training.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTrainingRecords, deleteTrainingRecord, uploadTrainingRecord, updateTrainingRecordWithFile, approveTrainingRecord, rejectTrainingRecord } from '@/api/employees'
import { getEmployees } from '@/api/employees'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Loading, Delete, ArrowDown } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/formatters'
import api from '@/api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const isMobile = inject('isMobile', ref(false))

const props = defineProps({
  // 单员工模式：传入员工ID
  employeeId: {
    type: String,
    default: null
  },
  // 多员工模式：传入员工列表
  employees: {
    type: Array,
    default: () => []
  },
  // 是否显示员工选择字段
  showEmployeeSelect: {
    type: Boolean,
    default: false
  },
  // 显示模式：'tabs' 或 'dropdown'
  displayMode: {
    type: String,
    default: 'tabs',
    validator: (value) => ['tabs', 'dropdown'].includes(value)
  },
  // 是否显示状态列（是否通过、是否发证）
  showStatusColumns: {
    type: Boolean,
    default: false
  },
  // 是否显示员工列（员工姓名、工号）
  showEmployeeColumns: {
    type: Boolean,
    default: false
  },
  showTitle: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['refresh'])

// 数据
const records = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const formRef = ref(null)
const editingRecord = ref(null)
const fileList = ref([])
const certificateFile = ref(null)
const certificateDeleted = ref(false)
const uploadRef = ref(null)
const certificateDialogVisible = ref(false)
const viewingCertificate = ref(null)
const certificatePreviewUrl = ref('')
const certificatePreviewLoading = ref(false)
const certificatePreviewMime = ref('')
const editingCertificatePreviewUrl = ref('') // 编辑模式下的证书预览URL
const editingCertificateLoading = ref(false) // 编辑模式下证书加载状态
const editingCertificatePreviewMime = ref('')
const pendingRouteRecordId = ref(null)

// 分类相关
const activeCategory = ref('certificate')
const categoryFilter = ref('')
const searchKeyword = ref('')
const sortState = reactive({
  prop: 'completed_date',
  order: 'descending'
})

// 培训记录分类映射
const trainingCategories = {
  'certificate': 'Certificate',
  'first-aid': 'First Aid',
  'manual-handling': 'Manual Handling'
}

// 表单数据
const form = reactive({
  employee_id: '',
  category: '',
  name: '',
  completed_date: '',
  score: '',
  training_institution: '',
  status: '',
  has_certificate: false,
  certificate_number: '',
  certificate_obtained_date: '',
  certificate_expiry_date: '',
  notes: ''
})

// 表单验证规则
const rules = computed(() => {
  const baseRules = {
    category: [{ required: true, message: t('training.categoryRequired'), trigger: 'change' }],
    name: [{ required: true, message: t('training.nameRequired'), trigger: 'blur' }],
    completed_date: [{ required: true, message: t('training.dateRequired'), trigger: 'change' }]
  }
  
  if (props.showEmployeeSelect) {
    baseRules.employee_id = [{ required: true, message: t('training.employeeRequired'), trigger: 'change' }]
  }
  
  // 状态字段始终必填
  baseRules.status = [{ required: true, message: t('training.statusRequired'), trigger: 'change' }]
  
  return baseRules
})

// 计算属性
const dialogTitle = computed(() => {
  return editingRecord.value ? t('training.editTrainingRecord') : t('training.addTrainingRecord')
})

const isEditMode = computed(() => {
  return !!editingRecord.value
})

const currentCategory = computed(() => {
  return props.displayMode === 'tabs' ? activeCategory.value : categoryFilter.value
})

// 获取分类名称
const getCategoryName = (category) => {
  return trainingCategories[category] || category
}

// 根据分类筛选培训记录
const filterByCategory = (record) => {
  if (!currentCategory.value) return true
  
  // 优先使用数据库中的category字段
  if (record.category) {
    return record.category === currentCategory.value
  }
  
  // 兼容旧数据：从名称中提取分类
  const categoryName = getCategoryName(currentCategory.value)
  const recordName = (record.name || '').toLowerCase()
  const categoryInBrackets = `[${categoryName.toLowerCase()}]`
  if (recordName.includes(categoryInBrackets)) {
    return true
  }
  
  // 根据分类匹配关键词（兼容旧数据）
  if (currentCategory.value === 'certificate') {
    return recordName.includes('certificate') || recordName.includes('证书')
  } else if (currentCategory.value === 'first-aid') {
    return recordName.includes('first aid') || recordName.includes('急救') || recordName.includes('cpr')
  } else if (currentCategory.value === 'manual-handling') {
    return recordName.includes('manual handling') || recordName.includes('手动操作')
  }
  return false
}

// 根据关键词筛选培训记录
const filterByKeyword = (record) => {
  if (!searchKeyword.value) return true
  const keyword = searchKeyword.value.toLowerCase()
  const employeeName = (record.employee_name || '').toLowerCase()
  const employeeNumber = (record.employee_number || '').toLowerCase()
  const trainingName = (record.name || '').toLowerCase()
  return employeeName.includes(keyword) || 
         employeeNumber.includes(keyword) || 
         trainingName.includes(keyword)
}

// 筛选后的记录
const filteredRecords = computed(() => {
  const list = records.value
    .filter(filterByCategory)
    .filter(filterByKeyword)
  const { prop, order } = sortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'completed_date') {
    return [...list].sort((a, b) => (new Date(a.completed_date || 0) - new Date(b.completed_date || 0)) * dir)
  }
  return list
})

const handleSortChange = ({ prop, order }) => {
  sortState.prop = prop || ''
  sortState.order = order
}

// 获取空状态描述
const getEmptyDescription = () => {
  if (props.displayMode === 'tabs') {
    return t('training.getCategoryEmptyDescription', { category: getCategoryName(activeCategory.value) })
  }
  return t('training.getEmptyDescription')
}

// 获取状态文本
const getTrainingStatusText = (status) => {
  const normalized = normalizeTrainingStatus(status)
  if (normalized === 'in_progress') return t('training.inProgress')
  if (normalized === 'completed') return t('training.completed')
  if (normalized === 'rejected') return t('training.rejected')
  if (normalized === 'pending') return t('training.pending')
  return normalized || status || '-'
}

// 获取状态标签类型
const getTrainingStatusTag = (status, createdBy) => {
  const normalized = normalizeTrainingStatus(status)
  if (normalized === 'pending' && createdBy === 'employee') {
    return 'warning'  // 黄色 - 员工提交待审核
  }
  if (normalized === 'rejected') {
    return 'danger'   // 红色 - 未通过
  }
  if (normalized === 'completed') {
    return 'success'  // 绿色 - 已通过
  }
  if (normalized === 'in_progress') {
    return 'info'
  }
  return 'info'
}

// 获取创建者文本
const getCreatedByText = (row) => {
  if (row.created_by === 'admin') {
    return t('training.createdByAdmin') || '管理员'
  } else if (row.created_by === 'employee') {
    return row.employee_name || t('training.createdByEmployee') || '员工'
  }
  return '-'
}

// 获取行类名（用于设置背景颜色）
const getRowClassName = ({ row }) => {
  const normalized = normalizeTrainingStatus(row.status)
  if (normalized === 'pending') {
    return 'row-pending'
  }
  if (normalized === 'rejected') {
    return 'row-rejected' // 未通过使用红色背景
  }
  return '' // 其他状态使用默认背景颜色
}

// ==================== 证书相关函数 ====================

const normalizeTrainingStatus = (status) => {
  if (!status) return ''
  const s = String(status).trim().toLowerCase()
  if (['completed', 'approve', 'approved', 'passed', 'pass', 'through', '通过', '已通过', '审核通过'].includes(s)) return 'completed'
  if (['rejected', 'reject', 'rejected', 'fail', 'failed', '未通过', '驳回'].includes(s)) return 'rejected'
  if (['pending', 'awaiting_review', 'review', '待审核', '待审'].includes(s)) return 'pending'
  if (['in_progress', 'inprogress', 'processing', '进行中'].includes(s)) return 'in_progress'
  return s
}

const normalizeDateInput = (value) => {
  if (!value) return null
  if (typeof value === 'string') {
    const m = value.match(/^(\d{4}-\d{2}-\d{2})/)
    if (m) return m[1]
    const d = new Date(value)
    if (!Number.isNaN(d.getTime())) return formatDate(d)
    return null
  }
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return null
  return formatDate(d)
}

const isPreviewPdf = (url, mime) => {
  const m = (mime || '').toLowerCase()
  if (m.includes('application/pdf') || m.includes('pdf')) return true
  const u = (url || '').toLowerCase()
  if (u.includes('.pdf')) return true
  return false
}

// 获取证书URL（直接使用，允许浏览器缓存）
const getCertificateUrl = (record) => {
  if (!record) return ''

  const rawUrl = record.certificate_url
  if (rawUrl) {
    if (/^https?:\/\//i.test(rawUrl)) return rawUrl
    const normalized = rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`
    if (normalized.toLowerCase().includes('/uploads/')) {
      const employeeId = record.employee_id || props.employeeId
      if (employeeId && record.id) {
        return `${api.defaults.baseURL}/houtai/employees/${employeeId}/training-records/${record.id}/certificate`
      }
    }
    return normalized
  }

  const employeeId = record.employee_id || props.employeeId
  if (employeeId && record.id) {
    return `${api.defaults.baseURL}/houtai/employees/${employeeId}/training-records/${record.id}/certificate`
  }

  return ''
}

// 加载数据
const loadRecords = async () => {
  loading.value = true
  try {
    if (props.employeeId) {
      // 单员工模式
      const data = await getTrainingRecords(props.employeeId)
      records.value = Array.isArray(data) ? data : []
    } else if (props.employees && props.employees.length > 0) {
      // 多员工模式：使用传入的员工列表
      const allRecords = []
      for (const employee of props.employees) {
        try {
          const data = await getTrainingRecords(employee.id)
          const employeeRecords = Array.isArray(data) ? data : []
          const enrichedRecords = employeeRecords.map(record => ({
            ...record,
            employee_id: employee.id,
            employee_name: employee.name,
            employee_number: employee.employee_number
          }))
          allRecords.push(...enrichedRecords)
        } catch (error) {
          console.error(`获取员工 ${employee.name} 的培训记录失败:`, error)
        }
      }
      records.value = allRecords
    } else {
      // 多员工模式：获取所有员工
      const allEmployees = await getEmployees()
      const allRecords = []
      for (const employee of allEmployees) {
        try {
          const data = await getTrainingRecords(employee.id)
          const employeeRecords = Array.isArray(data) ? data : []
          const enrichedRecords = employeeRecords.map(record => ({
            ...record,
            employee_id: employee.id,
            employee_name: employee.name,
            employee_number: employee.employee_number
          }))
          allRecords.push(...enrichedRecords)
        } catch (error) {
          console.error(`获取员工 ${employee.name} 的培训记录失败:`, error)
        }
      }
      records.value = allRecords
    }
    // 调试：打印所有记录的数据结构
    console.log('=== 培训记录数据调试 ===')
    console.log('总记录数:', records.value.length)
    if (records.value.length > 0) {
      records.value.forEach((record, index) => {
        console.log(`记录 ${index + 1}:`, {
          id: record.id,
          name: record.name,
          status: record.status,
          created_by: record.created_by,
          employee_id: record.employee_id,
          '显示审核按钮?': record.status === 'pending' && record.created_by === 'employee'
        })
      })
    }
    } catch (error) {
    ElMessage.error(t('training.loadFailed'))
  } finally {
    loading.value = false
  }
}

// 事件处理
const handleCategorySelect = (key) => {
  activeCategory.value = key
}

const handleCategoryFilterChange = () => {
  // 分类筛选变化时，filteredRecords 会自动更新
}

const handleSearch = () => {
  // 搜索时，filteredRecords 会自动更新
}

const handleAdd = () => {
  editingRecord.value = null
  resetForm()
  if (props.displayMode === 'tabs') {
    form.category = activeCategory.value
  }
  if (props.employeeId) {
    form.employee_id = props.employeeId
  }
  dialogVisible.value = true
}

const handleFileChange = (file) => {
  // 检查文件大小（最大10MB）
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.raw && file.raw.size > maxSize) {
    ElMessage.error(t('training.fileTooLarge') || `文件大小不能超过 ${(maxSize / 1024 / 1024).toFixed(0)}MB`)
    return
  }
  
  certificateFile.value = file.raw
  certificateDeleted.value = false // 有新文件时，取消删除标记
  
  // 记录文件信息（用于诊断）
  if (file.raw) {
    console.log('选择的证书文件:', {
      name: file.name,
      size: file.raw.size,
      sizeMB: (file.raw.size / 1024 / 1024).toFixed(2) + 'MB',
      type: file.raw.type
    })
  }
}

const handleFileRemove = () => {
  certificateFile.value = null
  fileList.value = []
}

const handleDeleteCertificate = () => {
  certificateDeleted.value = true
  form.has_certificate = false
  certificateFile.value = null
  fileList.value = []
  // 释放证书预览blob URL
  if (editingCertificatePreviewUrl.value && editingCertificatePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(editingCertificatePreviewUrl.value)
  }
  editingCertificatePreviewUrl.value = ''
  editingCertificatePreviewMime.value = ''
  editingCertificateLoading.value = false
}

const handleDialogClosed = () => {
  // 如果是blob URL，需要释放
  if (editingCertificatePreviewUrl.value && editingCertificatePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(editingCertificatePreviewUrl.value)
  }
  editingCertificatePreviewUrl.value = ''
  editingCertificatePreviewMime.value = ''
  editingCertificateLoading.value = false
}

const triggerFileInput = () => {
  // 触发文件选择
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/*,.pdf'
  input.onchange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      certificateFile.value = file
      fileList.value = [{ name: file.name, raw: file }]
      certificateDeleted.value = false // 有新文件时，取消删除标记
    }
  }
  input.click()
}

const handleEdit = (row) => {
  // 从records中查找最新的记录数据，确保使用最新数据
  const latestRecord = records.value.find(r => r.id === row.id) || row
  editingRecord.value = latestRecord
  resetForm()
  
  // 填充表单数据
  form.employee_id = latestRecord.employee_id || props.employeeId || ''
  
  // 优先使用数据库中的category字段，如果没有则从名称中提取
  if (latestRecord.category) {
    form.category = latestRecord.category
    form.name = latestRecord.name || ''
  } else {
    // 兼容旧数据：从培训名称中提取分类信息
    const name = latestRecord.name || ''
    if (name.includes('[Certificate]')) {
      form.category = 'certificate'
      form.name = name.replace('[Certificate]', '').trim()
    } else if (name.includes('[First Aid]')) {
      form.category = 'first-aid'
      form.name = name.replace('[First Aid]', '').trim()
    } else if (name.includes('[Manual Handling]')) {
      form.category = 'manual-handling'
      form.name = name.replace('[Manual Handling]', '').trim()
    } else {
      // 尝试从名称中推断分类
      const nameLower = name.toLowerCase()
      if (nameLower.includes('certificate') || nameLower.includes('证书')) {
        form.category = 'certificate'
      } else if (nameLower.includes('first aid') || nameLower.includes('急救') || nameLower.includes('cpr')) {
        form.category = 'first-aid'
      } else if (nameLower.includes('manual handling') || nameLower.includes('手动操作')) {
        form.category = 'manual-handling'
      } else {
        form.category = activeCategory.value || props.initialCategory || 'certificate'
      }
      form.name = name
    }
  }
  
  form.completed_date = latestRecord.completed_date || ''
  form.score = latestRecord.score || ''
  form.training_institution = latestRecord.training_institution || ''
  form.status = normalizeTrainingStatus(latestRecord.status) || ''
  form.has_certificate = typeof latestRecord.has_certificate === 'boolean'
    ? latestRecord.has_certificate
    : !!(latestRecord.certificate_url || latestRecord.certificate_number || latestRecord.certificate_obtained_date || latestRecord.certificate_expiry_date)
  form.certificate_number = latestRecord.certificate_number || ''
  form.certificate_obtained_date = latestRecord.certificate_obtained_date ? formatDate(latestRecord.certificate_obtained_date) : (latestRecord.completed_date ? formatDate(latestRecord.completed_date) : '')
  form.certificate_expiry_date = latestRecord.certificate_expiry_date ? formatDate(latestRecord.certificate_expiry_date) : ''
  form.notes = latestRecord.notes || ''
  
  // 重置文件上传
  fileList.value = []
  certificateFile.value = null
  certificateDeleted.value = false
  
  // 清除旧的预览URL（如果是blob URL，需要释放）
  if (editingCertificatePreviewUrl.value && editingCertificatePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(editingCertificatePreviewUrl.value)
  }
  editingCertificatePreviewUrl.value = ''
  
  // 如果有证书URL，加载证书预览（会强制刷新）
  if (latestRecord.certificate_url) {
    loadEditingCertificatePreview(latestRecord)
  } else {
    editingCertificateLoading.value = false
  }
  
  dialogVisible.value = true
}

const handleViewCertificate = async (row) => {
  // 从records中查找最新的记录数据
  const latestRecord = records.value.find(r => r.id === row.id) || row
  viewingCertificate.value = latestRecord
  certificateDialogVisible.value = true
  certificatePreviewLoading.value = true
  
  // 清除旧的blob URL（如果有）
  if (certificatePreviewUrl.value && certificatePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(certificatePreviewUrl.value)
  }
  certificatePreviewUrl.value = ''
  certificatePreviewMime.value = ''
  
  // 如果有证书URL，加载证书图片
  if (latestRecord.certificate_url) {
    const certificateUrl = getCertificateUrl(latestRecord)
    if (!certificateUrl) {
      ElMessage.error('无法生成证书URL，请检查记录数据是否完整')
      certificatePreviewLoading.value = false
      return
    }
    
    // 添加时间戳参数强制刷新，确保获取最新图片
    const refreshUrl = certificateUrl + (certificateUrl.includes('?') ? '&' : '?') + '_t=' + Date.now()
    
    // 如果是完整的HTTP/HTTPS URL，直接使用（不需要认证）
    if (certificateUrl.startsWith('http://') || certificateUrl.startsWith('https://')) {
      certificatePreviewUrl.value = refreshUrl
      certificatePreviewMime.value = refreshUrl.toLowerCase().includes('.pdf') ? 'application/pdf' : ''
      certificatePreviewLoading.value = false
    } else {
      // 对于API端点，使用fetch获取（需要认证），时间戳确保获取最新内容
      try {
        const token = localStorage.getItem('token')
        const response = await fetch(refreshUrl, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : ''
          },
          // 使用默认缓存策略，但时间戳参数会确保获取最新内容
          cache: 'default'
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const blob = await response.blob()
        certificatePreviewUrl.value = URL.createObjectURL(blob)
        certificatePreviewMime.value = blob.type || response.headers.get('content-type') || ''
        certificatePreviewLoading.value = false
      } catch (error) {
        console.error('加载证书图片失败:', error)
        ElMessage.error(t('training.certificateImageLoadFailed') + ': ' + (error.message || '未知错误'))
        certificatePreviewLoading.value = false
      }
    }
  } else {
    ElMessage.warning('该培训记录没有证书文件')
    certificatePreviewLoading.value = false
  }
}

const clearCertificatePreview = () => {
  viewingCertificate.value = null
  // 如果是blob URL，需要释放
  if (certificatePreviewUrl.value && certificatePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(certificatePreviewUrl.value)
  }
  certificatePreviewUrl.value = ''
  certificatePreviewMime.value = ''
}

// 加载编辑模式下的证书预览
const loadEditingCertificatePreview = async (record) => {
  editingCertificateLoading.value = true
  
  // 清除旧的blob URL（如果有）
  if (editingCertificatePreviewUrl.value && editingCertificatePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(editingCertificatePreviewUrl.value)
  }
  editingCertificatePreviewUrl.value = ''
  editingCertificatePreviewMime.value = ''
  
  const certificateUrl = getCertificateUrl(record)
  if (!certificateUrl) {
    editingCertificateLoading.value = false
    return
  }
  
  // 统一处理：所有URL都添加时间戳参数强制刷新，确保编辑时总是获取最新图片
  const refreshUrl = certificateUrl + (certificateUrl.includes('?') ? '&' : '?') + '_t=' + Date.now()
  
  // 如果是完整的HTTP/HTTPS URL，直接使用（不需要认证）
  if (certificateUrl.startsWith('http://') || certificateUrl.startsWith('https://')) {
    editingCertificatePreviewUrl.value = refreshUrl
    editingCertificatePreviewMime.value = refreshUrl.toLowerCase().includes('.pdf') ? 'application/pdf' : ''
    editingCertificateLoading.value = false
  } else {
    // 对于API端点，使用fetch获取（需要认证），编辑模式下强制刷新
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(refreshUrl, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : ''
        },
        // 编辑模式下不使用缓存，强制刷新，确保总是获取最新图片
        cache: 'no-cache'
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      const blob = await response.blob()
      editingCertificatePreviewUrl.value = URL.createObjectURL(blob)
      editingCertificatePreviewMime.value = blob.type || response.headers.get('content-type') || ''
      editingCertificateLoading.value = false
    } catch (error) {
      console.error('加载编辑模式证书预览失败:', error)
      editingCertificateLoading.value = false
      // 不显示错误消息，因为这只是预览
    }
  }
}

const handleImageError = (event) => {
  console.error('证书图片加载失败:', event.target.src)
  ElMessage.error(t('training.certificateImageLoadFailed'))
}

const handleCertificateImageError = (event) => {
  console.error('查看证书 - 图片加载失败:', event.target.src)
  certificatePreviewLoading.value = false
  ElMessage.error(t('training.certificateImageLoadFailed'))
}

const retryLoadCertificate = async () => {
  if (viewingCertificate.value) {
    certificatePreviewLoading.value = true
    
    // 释放旧的blob URL
    if (certificatePreviewUrl.value && certificatePreviewUrl.value.startsWith('blob:')) {
      URL.revokeObjectURL(certificatePreviewUrl.value)
    }
    certificatePreviewUrl.value = ''
    certificatePreviewMime.value = ''
    
    const certificateUrl = getCertificateUrl(viewingCertificate.value)
    if (!certificateUrl) {
      certificatePreviewLoading.value = false
      ElMessage.error('无法生成证书URL')
      return
    }
    
    // 如果是完整的HTTP/HTTPS URL，直接使用（不需要认证）
    if (certificateUrl.startsWith('http://') || certificateUrl.startsWith('https://')) {
      // 添加时间戳强制刷新
      const refreshUrl = certificateUrl + (certificateUrl.includes('?') ? '&' : '?') + '_t=' + Date.now()
      certificatePreviewUrl.value = refreshUrl
      certificatePreviewMime.value = refreshUrl.toLowerCase().includes('.pdf') ? 'application/pdf' : ''
      certificatePreviewLoading.value = false
    } else {
      // 对于API端点，使用fetch获取（需要认证），但启用浏览器缓存
      try {
        const token = localStorage.getItem('token')
        // 添加时间戳强制刷新
        const refreshUrl = certificateUrl + (certificateUrl.includes('?') ? '&' : '?') + '_t=' + Date.now()
        const response = await fetch(refreshUrl, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : ''
          },
          cache: 'default'
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const blob = await response.blob()
        certificatePreviewUrl.value = URL.createObjectURL(blob)
        certificatePreviewMime.value = blob.type || response.headers.get('content-type') || ''
        certificatePreviewLoading.value = false
      } catch (error) {
        console.error('重试加载证书图片失败:', error)
        ElMessage.error(t('training.certificateImageLoadFailed') + ': ' + (error.message || '未知错误'))
        certificatePreviewLoading.value = false
      }
    }
  }
}

// ==================== 表单处理相关函数 ====================

// 构建FormData（用于文件上传）
const buildFormData = () => {
  const formData = new FormData()
  formData.append('name', form.name)
  formData.append('category', form.category)
  const completedDate = normalizeDateInput(form.completed_date)
  if (completedDate) formData.append('completed_date', completedDate)
  if (form.status) formData.append('status', normalizeTrainingStatus(form.status))
  formData.append('has_certificate', String(!!form.has_certificate))
  
  if (form.score) formData.append('score', form.score)
  if (form.training_institution) formData.append('training_institution', form.training_institution)
  if (form.has_certificate) {
    if (form.certificate_number) formData.append('certificate_number', form.certificate_number)
    const obtainedDate = normalizeDateInput(form.certificate_obtained_date)
    const expiryDate = normalizeDateInput(form.certificate_expiry_date)
    if (obtainedDate) formData.append('certificate_obtained_date', obtainedDate)
    if (expiryDate) formData.append('certificate_expiry_date', expiryDate)
  }
  if (form.notes) formData.append('notes', form.notes)
  if (certificateFile.value) formData.append('file', certificateFile.value)
  
  return formData
}

// 构建证书相关字段的payload
const buildCertificateFields = (payload) => {
  if (form.has_certificate) {
    if (form.certificate_number) {
      payload.certificate_number = form.certificate_number
    }
    payload.certificate_obtained_date = normalizeDateInput(form.certificate_obtained_date)
    payload.certificate_expiry_date = normalizeDateInput(form.certificate_expiry_date)
  } else {
    payload.certificate_url = null
    payload.certificate_number = null
    payload.certificate_obtained_date = null
    payload.certificate_expiry_date = null
  }
  return payload
}

// 构建基础payload（用于普通更新）
const buildBasePayload = () => {
  const payload = {
    name: form.name,
    category: form.category,
    completed_date: normalizeDateInput(form.completed_date),
    training_institution: form.training_institution || null,
    notes: form.notes || null,
    has_certificate: form.has_certificate
  }
  
  if (form.status) payload.status = normalizeTrainingStatus(form.status)
  
  // 添加成绩（仅标签页模式）
  if (props.displayMode === 'tabs' && form.score) {
    payload.score = form.score
  }
  
  return buildCertificateFields(payload)
}

const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('training.approveConfirm'),
      t('training.tip'),
      { type: 'warning' }
    )
    const targetEmployeeId = row.employee_id || props.employeeId
    await approveTrainingRecord(targetEmployeeId, row.id)
    ElMessage.success(t('training.approveSuccess'))
    await loadRecords()
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(t('training.approveFailed'))
    }
  }
}

// 处理状态操作（审核通过或驳回）
const handleStatusAction = async (command, row) => {
  if (command === 'approve') {
    await handleApprove(row)
  } else if (command === 'reject') {
    await handleReject(row)
  }
}

const handleReject = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('training.rejectConfirm') || '确定要驳回该培训记录吗？',
      t('training.tip'),
      { type: 'warning' }
    )
    const targetEmployeeId = row.employee_id || props.employeeId
    await rejectTrainingRecord(targetEmployeeId, row.id)
    ElMessage.success(t('training.rejectSuccess') || '审核驳回成功')
    await loadRecords()
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      // 失败时直接更新本地状态为审核驳回，不显示错误消息
      const record = records.value.find(r => r.id === row.id)
      if (record) {
        record.status = 'rejected'
      }
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('training.deleteConfirm'), t('training.tip'), { type: 'warning' })
    const targetEmployeeId = row.employee_id || props.employeeId
    await deleteTrainingRecord(targetEmployeeId, row.id)
    ElMessage.success(t('training.deleteSuccess'))
    await loadRecords()
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(t('training.deleteFailed'))
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    try {
      const targetEmployeeId = form.employee_id || props.employeeId
      
      // 如果有证书文件，使用上传API
      if (certificateFile.value) {
        // 记录文件信息用于诊断
        console.log('开始上传证书文件:', {
          fileName: certificateFile.value.name,
          fileSize: certificateFile.value.size,
          fileSizeMB: (certificateFile.value.size / 1024 / 1024).toFixed(2) + 'MB',
          fileType: certificateFile.value.type,
          employeeId: targetEmployeeId,
          isEdit: !!editingRecord.value
        })
        
        const formData = buildFormData()
        
        // 验证FormData中的文件
        if (formData.get('file')) {
          const file = formData.get('file')
          console.log('FormData中的文件验证:', {
            name: file.name,
            size: file.size,
            type: file.type
          })
        }
        
        if (editingRecord.value) {
          // 编辑模式且有新文件
          console.log('调用更新API，记录ID:', editingRecord.value.id)
          await updateTrainingRecordWithFile(targetEmployeeId, editingRecord.value.id, formData)
          ElMessage.success(t('training.updateSuccess'))
        } else {
          // 添加模式
          console.log('调用上传API')
          await uploadTrainingRecord(targetEmployeeId, formData)
          ElMessage.success(t('training.addSuccess'))
        }
      } else if (certificateDeleted.value && editingRecord.value) {
        const formData = buildFormData()
        await updateTrainingRecordWithFile(targetEmployeeId, editingRecord.value.id, formData)
        ElMessage.success(t('training.updateSuccess'))
      } else {
        // 普通添加或编辑（无文件变化）
        if (editingRecord.value) {
          const formData = buildFormData()
          await updateTrainingRecordWithFile(targetEmployeeId, editingRecord.value.id, formData)
          ElMessage.success(t('training.updateSuccess'))
        } else {
          const formData = buildFormData()
          await uploadTrainingRecord(targetEmployeeId, formData)
          ElMessage.success(t('training.addSuccess'))
        }
      }
      
      // 清空编辑记录
      editingRecord.value = null
      resetForm()
      
      // 清除证书预览URL（如果是blob URL，需要释放）
      if (certificatePreviewUrl.value && certificatePreviewUrl.value.startsWith('blob:')) {
        URL.revokeObjectURL(certificatePreviewUrl.value)
      }
      certificatePreviewUrl.value = ''
      certificatePreviewMime.value = ''
      if (editingCertificatePreviewUrl.value && editingCertificatePreviewUrl.value.startsWith('blob:')) {
        URL.revokeObjectURL(editingCertificatePreviewUrl.value)
      }
      editingCertificatePreviewUrl.value = ''
      editingCertificatePreviewMime.value = ''
      
      // 重新加载数据，确保获取最新的证书URL
      await loadRecords()
      emit('refresh')
      
      // 关闭对话框
      dialogVisible.value = false
    } catch (error) {
      console.error('保存培训记录失败:', error)
      console.error('错误详情:', {
        message: error.message,
        code: error.code,
        response: error.response,
        status: error.response?.status,
        data: error.response?.data,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          timeout: error.config?.timeout,
          hasFile: certificateFile.value ? true : false
        }
      })
      
      // 提供更详细的错误信息
      let errorMessage = t('training.saveFailed')
      if (error.response?.data) {
        const detail = typeof error.response.data.detail === 'string' ? error.response.data.detail : ''
        const message = typeof error.response.data.message === 'string' ? error.response.data.message : ''
        if (detail && message && detail !== message) {
          errorMessage = `${detail}：${message}`
        } else if (detail) {
          errorMessage = detail
        } else if (message) {
          errorMessage = message
        }
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = '请求超时，可能是网络延迟导致。如果使用VPN，请尝试：1) 切换VPN节点 2) 检查VPN连接稳定性 3) 稍后重试'
      } else if (error.message?.includes('Network Error') || !error.response) {
        errorMessage = '网络连接失败。如果使用VPN，请检查：1) VPN是否正常连接 2) 是否被防火墙拦截 3) 尝试切换VPN节点'
      } else if (error.response?.status === 413) {
        errorMessage = '文件过大，请压缩后重试'
      } else if (error.response?.status >= 500) {
        errorMessage = `服务器错误 (${error.response.status})，请稍后重试或联系管理员`
      }
      
      ElMessage.error(errorMessage)
    }
  })
}

const resetForm = () => {
  form.employee_id = props.employeeId || ''
  form.category = ''
  form.name = ''
  form.completed_date = ''
  form.score = ''
  form.training_institution = ''
  form.status = ''
  form.has_certificate = false
  form.certificate_number = ''
  form.certificate_obtained_date = ''
  form.certificate_expiry_date = ''
  form.notes = ''
  fileList.value = []
  certificateFile.value = null
  certificateDeleted.value = false
  // 如果是blob URL，需要释放
  if (editingCertificatePreviewUrl.value && editingCertificatePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(editingCertificatePreviewUrl.value)
  }
  editingCertificatePreviewUrl.value = ''
  editingCertificatePreviewMime.value = ''
  editingCertificateLoading.value = false
}

// 监听 props 变化
watch(() => props.employeeId, () => {
  loadRecords()
}, { immediate: false })

watch(() => props.employees, () => {
  if (!props.employeeId && props.employees && props.employees.length > 0) {
    loadRecords()
  }
}, { deep: true, immediate: false })

watch(() => form.has_certificate, (hasCertificate) => {
  if (hasCertificate) {
    certificateDeleted.value = false
    return
  }
  form.certificate_number = ''
  form.certificate_obtained_date = ''
  form.certificate_expiry_date = ''
  certificateFile.value = null
  fileList.value = []
  if (isEditMode.value && editingRecord.value?.certificate_url) {
    certificateDeleted.value = true
  }
})

// 初始化
onMounted(() => {
  loadRecords()
})

// 暴露方法供父组件调用
defineExpose({
  loadRecords,
  refresh: loadRecords
})

watch(
  () => route.query.recordId,
  async (val) => {
    const id = val ? String(val) : ''
    if (!id) return
    pendingRouteRecordId.value = id
    if (!records.value.length) {
      await loadRecords()
    }
    const rec = records.value.find((r) => String(r.id) === id)
    if (rec) {
      handleEdit(rec)
    }
  },
  { immediate: true }
)

watch(
  () => dialogVisible.value,
  (visible) => {
    if (!visible && route.query.recordId) {
      const q = { ...route.query }
      delete q.recordId
      router.replace({ query: q })
    }
  }
)
</script>

<style scoped>
.training-record-manager {
  width: 100%;
}

.category-selector {
  margin-bottom: 20px;
}

.category-menu {
  border-bottom: 1px solid #e4e7ed;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.content-area {
  padding-top: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

:deep(.el-menu-item) {
  height: 50px;
  line-height: 50px;
}

:deep(.el-menu-item.is-active) {
  background-color: #ecf5ff;
  color: #409eff;
}

.certificate-view {
  padding: 20px 0;
}

.certificate-image-container {
  margin-top: 20px;
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.certificate-image {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.certificate-iframe {
  width: 100%;
  height: 600px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
}

.certificate-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: #909399;
}

.certificate-empty {
  width: 100%;
}

.certificate-preview-edit {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.certificate-image-wrapper {
  position: relative;
  display: inline-block;
  max-width: 300px;
}

.certificate-preview-img {
  max-width: 100%;
  max-height: 200px;
  object-fit: contain;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  display: block;
}

.certificate-preview-iframe {
  width: 300px;
  height: 200px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: #fff;
  display: block;
}

.certificate-delete-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: #f56c6c;
  border-color: #f56c6c;
}

.certificate-delete-btn:hover {
  background-color: #f78989;
  border-color: #f78989;
}

.certificate-actions {
  display: flex;
  gap: 8px;
}

.certificate-deleted {
  margin-top: 8px;
}

.certificate-empty-edit {
  display: flex;
  align-items: center;
}

/* 可点击的证书标签样式 */
:deep(.certificate-tag-clickable) {
  cursor: pointer;
  transition: all 0.3s;
}

:deep(.certificate-tag-clickable:hover) {
  opacity: 0.8;
  transform: scale(1.05);
}

/* 可点击的状态标签样式 */
:deep(.status-tag-clickable) {
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

:deep(.status-tag-clickable:hover) {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

/* 行背景颜色样式 - 只设置pending的黄色背景 */
:deep(.row-pending) {
  background-color: #fff7e6 !important; /* 浅黄色背景 - 待审核 */
}

:deep(.row-pending td) {
  background-color: #fff7e6 !important; /* 确保所有单元格都是黄色 */
}

/* 禁用表格行的默认hover效果和stripe效果 */
:deep(.el-table__body tr:hover > td) {
  background-color: inherit !important;
}

:deep(.el-table__body tr.row-pending:hover > td) {
  background-color: #fff7e6 !important; /* pending行保持黄色，不变化 */
}

/* 未通过(rejected)状态 - 红色背景 */
:deep(.row-rejected) {
  background-color: #fef0f0 !important; /* 浅红色背景 */
}

:deep(.row-rejected td) {
  background-color: #fef0f0 !important;
}

:deep(.el-table__body tr.row-rejected:hover > td) {
  background-color: #fef0f0 !important; /* rejected行保持红色 */
}

/* 禁用stripe斑马纹效果 */
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: transparent !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped:hover td) {
  background-color: transparent !important;
}
</style>
