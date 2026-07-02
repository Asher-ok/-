<template>
  <div class="employee-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('employeeList.title') }}</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            {{ $t('employeeList.addEmployee') }}
          </el-button>
        </div>
      </template>
      
      <div class="table-toolbar">
        <el-select v-model="departmentFilter" clearable class="dept-select" :placeholder="$t('employeeList.department')">
          <el-option v-for="opt in departmentOptions" :key="opt" :label="opt" :value="opt" />
        </el-select>
        <el-input
          v-model="searchName"
          :placeholder="t('employeeList.searchPlaceholder')"
          clearable
          class="search-input"
        />
      </div>

      <el-table :data="filteredEmployees" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="employee_number" :label="$t('employeeList.employeeNumber')" width="130">
          <template #default="{ row }">
            <span class="clickable-with-dot">
              <span v-if="row.has_update || row.has_qualification_update" class="row-dot" />
              <el-link type="primary" class="clickable-text" :underline="true" @click="handleView(row)">{{ row.employee_number || '-' }}</el-link>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('employeeList.name')" width="130">
          <template #default="{ row }">
            <span class="clickable-with-dot">
              <span v-if="row.has_update || row.has_qualification_update" class="row-dot" />
              <el-link type="primary" class="clickable-text" :underline="true" @click="handleView(row)">{{ row.name || '-' }}</el-link>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="department" :label="$t('employeeList.department')" width="130" />
        <el-table-column prop="phone" :label="$t('employeeList.phone')" width="160" />
        <el-table-column prop="email" :label="$t('employeeList.email')" min-width="270" />
        <el-table-column :label="$t('employeeList.expiringQualifications')" min-width="320" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ getEmployeeExpiringQualificationsText(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('employeeList.operations')" width="220" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="handleEdit(row)">
                {{ $t('employeeList.edit') }}
              </el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">
                {{ $t('employeeList.delete') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="720px"
      @close="handleDialogClose"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="auto">
        <el-form-item :label="$t('employeeList.name')" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="$t('employeeList.employeeNumber')" prop="employee_number">
          <el-input v-model="form.employee_number" disabled />
        </el-form-item>
        <el-form-item :label="$t('employeeList.password')" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="form.id ? $t('employeeList.passwordPlaceholder') : $t('employeeList.passwordPlaceholderNew')"
          />
        </el-form-item>
        <el-form-item :label="$t('employeeList.department')" prop="department">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item :label="$t('employeeList.phone')" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item :label="$t('employeeList.email')" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({
  name: 'Employees'
})
import { ref, reactive, onMounted, onBeforeUnmount, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { getEmployees, createEmployee, updateEmployee, deleteEmployee, getExpiringTrainingRecords, getExpiredTrainingRecords } from '@/api/employees'
import { markUpdatesRead } from '@/api/updates'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { formatDateTimeToMinute } from '@/utils/formatters'

const { t } = useI18n()
const router = useRouter()
const isMobile = inject('isMobile', ref(false))
const employees = ref([])
const loading = ref(false)
const employeeTrainingExpiryPrimaryMap = ref(new Map())
const dialogVisible = ref(false)
const formRef = ref(null)
const searchName = ref('')
const departmentFilter = ref('')

const dialogTitle = computed(() => {
  return form.id ? t('employeeList.editEmployee') : t('employeeList.addEmployee')
})

const departmentOptions = computed(() => {
  const set = new Set()
  for (const emp of employees.value || []) {
    const dep = (emp?.department || '').toString().trim()
    if (dep) set.add(dep)
  }
  return [...set].sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))
})

const normalizeExpiryDate = (q) => {
  return q?.expiry_date || q?.certificate_expiry_date || q?.expires_at || q?.expire_at || q?.expired_at || q?.expiring_primary_expiry_date || ''
}

const parseTime = (v) => {
  if (!v) return Number.POSITIVE_INFINITY
  const d = new Date(v)
  const ms = d.getTime()
  if (!Number.isFinite(ms)) return Number.POSITIVE_INFINITY
  return ms
}

const normalizeTrainingExpiryRecord = (r) => {
  const certificateNumber = (r?.certificate_number || r?.certificateNo || r?.certificate_no || '').toString().trim() || null
  const expiryDate = normalizeExpiryDate(r) || null
  const expiryMs = parseTime(expiryDate)
  const qualificationName = (r?.name || r?.training_name || r?.qualification_name || r?.trainingName || '').toString().trim() || null
  const daysUntilExpiry = typeof r?.days_until_expiry === 'number' ? r.days_until_expiry : (typeof r?.daysUntilExpiry === 'number' ? r.daysUntilExpiry : null)
  const rank = daysUntilExpiry !== null ? (daysUntilExpiry <= 0 ? 0 : 1) : (Number.isFinite(expiryMs) ? (expiryMs <= Date.now() ? 0 : 1) : 2)
  if (!certificateNumber || !Number.isFinite(expiryMs)) return null
  return { certificateNumber, expiryDate, qualificationName, daysUntilExpiry, expiryMs, rank }
}

const getEmployeeIdFromTrainingExpiryRow = (r) => {
  const v = r?.employee_id ?? r?.employeeId ?? r?.employeeID ?? r?.employee?.id
  if (v === null || v === undefined) return null
  const id = String(v).trim()
  return id ? id : null
}

const loadEmployeeTrainingExpiryPrimary = async () => {
  try {
    const [expiringRaw, expiredRaw] = await Promise.all([
      getExpiringTrainingRecords(36500),
      getExpiredTrainingRecords()
    ])

    const expiring = Array.isArray(expiringRaw) ? expiringRaw : (Array.isArray(expiringRaw?.rows) ? expiringRaw.rows : (Array.isArray(expiringRaw?.data) ? expiringRaw.data : []))
    const expired = Array.isArray(expiredRaw) ? expiredRaw : (Array.isArray(expiredRaw?.rows) ? expiredRaw.rows : (Array.isArray(expiredRaw?.data) ? expiredRaw.data : []))

    const expiredByEmployee = new Map()
    for (const r of expired) {
      const empId = getEmployeeIdFromTrainingExpiryRow(r)
      if (!empId) continue
      const normalized = normalizeTrainingExpiryRecord(r)
      if (!normalized) continue
      const bucket = expiredByEmployee.get(empId) || []
      bucket.push(normalized)
      expiredByEmployee.set(empId, bucket)
    }

    const expiringByEmployee = new Map()
    for (const r of expiring) {
      const empId = getEmployeeIdFromTrainingExpiryRow(r)
      if (!empId) continue
      const normalized = normalizeTrainingExpiryRecord(r)
      if (!normalized) continue
      const bucket = expiringByEmployee.get(empId) || []
      bucket.push(normalized)
      expiringByEmployee.set(empId, bucket)
    }

    const primaryMap = new Map()
    const allEmployeeIds = new Set([...expiredByEmployee.keys(), ...expiringByEmployee.keys()])
    for (const empId of allEmployeeIds) {
      const expiredList = expiredByEmployee.get(empId) || []
      if (expiredList.length) {
        expiredList.sort((a, b) => a.expiryMs - b.expiryMs)
        primaryMap.set(empId, expiredList[0])
        continue
      }
      const expiringList = expiringByEmployee.get(empId) || []
      if (expiringList.length) {
        expiringList.sort((a, b) => a.expiryMs - b.expiryMs)
        primaryMap.set(empId, expiringList[0])
      }
    }

    employeeTrainingExpiryPrimaryMap.value = primaryMap
  } catch (e) {
    employeeTrainingExpiryPrimaryMap.value = new Map()
  }
}

const getEmployeePrimaryExpiring = (row) => {
  const mapPrimary = employeeTrainingExpiryPrimaryMap.value?.get?.(String(row?.id ?? '').trim())
  if (mapPrimary) return mapPrimary

  const direct = {
    certificateNumber: (row?.expiring_primary_certificate_number || '').toString().trim() || null,
    expiryDate: row?.expiring_primary_expiry_date || null,
    qualificationName: (row?.expiring_primary_qualification_name || '').toString().trim() || null,
    daysUntilExpiry: row?.expiring_primary_days_until_expiry
  }
  const hasDirect = direct.certificateNumber || direct.expiryDate || direct.qualificationName || typeof direct.daysUntilExpiry === 'number'
  if (hasDirect) {
    const ms = parseTime(direct.expiryDate)
    const normalizedDays = typeof direct.daysUntilExpiry === 'number' ? direct.daysUntilExpiry : null
    const rank = normalizedDays !== null ? (normalizedDays <= 0 ? 0 : 1) : (Number.isFinite(ms) ? (ms <= Date.now() ? 0 : 1) : 2)
    return { ...direct, expiryMs: ms, rank, daysUntilExpiry: normalizedDays }
  }

  const list = Array.isArray(row?.expiring_qualifications) ? row.expiring_qualifications : []
  if (!list.length) {
    return { certificateNumber: null, expiryDate: null, qualificationName: null, daysUntilExpiry: null, expiryMs: Number.POSITIVE_INFINITY, rank: 2 }
  }

  const candidates = list
    .map((q) => {
      const expiryDate = normalizeExpiryDate(q)
      const expiryMs = parseTime(expiryDate)
      const qualificationName = (q?.name || q?.qualification_name || q?.training_name || '').toString().trim() || null
      const certificateNumber = (q?.certificate_number || q?.certificateNo || q?.certificate_no || '').toString().trim() || null
      const daysUntilExpiry = typeof q?.days_until_expiry === 'number' ? q.days_until_expiry : null
      const rank = daysUntilExpiry !== null ? (daysUntilExpiry <= 0 ? 0 : 1) : (Number.isFinite(expiryMs) ? (expiryMs <= Date.now() ? 0 : 1) : 2)
      return { certificateNumber, expiryDate, qualificationName, daysUntilExpiry, expiryMs, rank }
    })
    .filter((c) => c.certificateNumber || c.qualificationName || Number.isFinite(c.expiryMs))

  if (!candidates.length) {
    return { certificateNumber: null, expiryDate: null, qualificationName: null, daysUntilExpiry: null, expiryMs: Number.POSITIVE_INFINITY, rank: 2 }
  }

  const expired = candidates.filter((c) => c.rank === 0 && Number.isFinite(c.expiryMs))
  if (expired.length) {
    expired.sort((a, b) => a.expiryMs - b.expiryMs)
    return expired[0]
  }

  const expiring = candidates.filter((c) => c.rank === 1 && Number.isFinite(c.expiryMs))
  if (expiring.length) {
    expiring.sort((a, b) => a.expiryMs - b.expiryMs)
    return expiring[0]
  }

  candidates.sort((a, b) => a.expiryMs - b.expiryMs)
  return candidates[0]
}

const filteredEmployees = computed(() => {
  const keyword = searchName.value.trim().toLowerCase()
  const dep = (departmentFilter.value || '').toString().trim()
  const base = keyword
    ? employees.value.filter((item) => {
    const name = (item?.name || '').toString().toLowerCase()
    return name.includes(keyword)
    })
    : employees.value

  const byDep = dep
    ? base.filter((item) => (item?.department || '').toString().trim() === dep)
    : base
  return [...byDep].sort((a, b) => parseTime(b?.created_at) - parseTime(a?.created_at))
})

const form = reactive({
  id: null,
  name: '',
  employee_number: '',
  password: '',
  department: '',
  phone: '',
  email: ''
})

const isCreate = computed(() => !form.id)

const rules = computed(() => {
  const base = {
    name: [{ required: true, message: t('employeeList.nameRequired'), trigger: 'blur' }],
    employee_number: [{ required: true, message: t('employeeList.employeeNumberRequired'), trigger: 'blur' }],
    password: [],
    department: [],
    phone: [{ required: true, message: t('employeeList.phoneRequired'), trigger: 'blur' }],
    email: [{ required: true, message: t('employeeList.emailRequired'), trigger: 'blur' }]
  }

  if (isCreate.value) {
    base.password = [{ required: true, message: t('employeeList.passwordRequired'), trigger: 'blur' }]
    base.department = [{ required: true, message: t('employeeList.departmentRequired'), trigger: 'blur' }]
  }

  return base
})

const loadEmployees = async () => {
  loading.value = true
  try {
    const result = await getEmployees()
    if (Array.isArray(result)) {
      employees.value = result
    } else if (Array.isArray(result?.rows)) {
      employees.value = result.rows
    } else if (Array.isArray(result?.data)) {
      employees.value = result.data
    } else {
      employees.value = []
    }
    await loadEmployeeTrainingExpiryPrimary()
  } catch (error) {
    ElMessage.error(t('employeeList.loadFailed'))
  } finally {
    loading.value = false
  }
}

const getEmployeeExpiringQualificationsText = (row) => {
  const primary = getEmployeePrimaryExpiring(row)
  if (primary.rank === 2) return '-'
  const cert = primary.certificateNumber || '-'
  const name = primary.qualificationName || ''
  const expiry = Number.isFinite(primary.expiryMs) ? formatDateTimeToMinute(primary.expiryDate) : '-'
  const left = name ? `${name}（${cert}）` : cert
  return `${left}${expiry && expiry !== '-' ? `：${expiry}` : ''}`
}

const getNextEmployeeNumber = () => {
  const nums = employees.value
    .map((e) => {
      const raw = e?.employee_number
      if (raw === null || raw === undefined) return NaN
      const n = Number.parseInt(String(raw), 10)
      return Number.isFinite(n) ? n : NaN
    })
    .filter((n) => Number.isFinite(n))
  const max = nums.length ? Math.max(...nums) : 0
  return String(max + 1).padStart(6, '0')
}

const handleAdd = () => {
  Object.assign(form, {
    id: null,
    name: '',
    employee_number: getNextEmployeeNumber(),
    password: '',
    department: '',
    phone: '',
    email: ''
  })
  dialogVisible.value = true
}

const handleView = (row) => {
  if (row?.has_update && row?.id) {
    markUpdatesRead('employee', row.id).catch(() => {})
    row.has_update = false
    try {
      window.dispatchEvent(new Event('updates-changed'))
    } catch {}
  }
  router.push(`/employees/${row.id}`)
}

const handleEdit = (row) => {
  Object.assign(form, { ...row, password: '' })
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('employeeList.deleteConfirm'), t('employeeList.tip'), {
      type: 'warning'
    })
    await deleteEmployee(row.id)
    ElMessage.success(t('employeeList.deleteSuccess'))
    loadEmployees()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('employeeList.deleteFailed'))
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (form.id) {
          const payload = { ...form }
          if (!payload.password) {
            delete payload.password
          }
          await updateEmployee(form.id, payload)
          ElMessage.success(t('employeeList.updateSuccess'))
        } else {
          const basePayload = { ...form }
          delete basePayload.id

          const payloadWithoutNumber = { ...basePayload }
          delete payloadWithoutNumber.employee_number

          try {
            await createEmployee(payloadWithoutNumber)
          } catch (err) {
            const status = err?.response?.status
            const detail = err?.response?.data?.detail || ''
            const detailText = String(detail).toLowerCase()
            const shouldRetryWithNumber =
              status === 422 ||
              status === 400 ||
              detailText.includes('employee_number') ||
              detailText.includes('employee number')

            if (!shouldRetryWithNumber) {
              throw err
            }

            const tryCreateWithNumber = async (employeeNumber) => {
              await createEmployee({ ...payloadWithoutNumber, employee_number: employeeNumber })
            }

            const nextNumber = form.employee_number || getNextEmployeeNumber()
            try {
              await tryCreateWithNumber(nextNumber)
            } catch (retryErr) {
              const retryStatus = retryErr?.response?.status
              const retryDetail = String(retryErr?.response?.data?.detail || '').toLowerCase()
              const maybeNumberConflict =
                retryStatus === 409 &&
                (retryDetail.includes('employee_number') || retryDetail.includes('employee number'))

              if (!maybeNumberConflict) {
                throw retryErr
              }

              const latestEmployees = await getEmployees()
              employees.value = Array.isArray(latestEmployees) ? latestEmployees : employees.value
              const refreshedNumber = getNextEmployeeNumber()
              form.employee_number = refreshedNumber
              await tryCreateWithNumber(refreshedNumber)
            }
          }

          ElMessage.success(t('employeeList.createSuccess'))
        }
        dialogVisible.value = false
        loadEmployees()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || t('employeeList.operationFailed'))
      }
    }
  })
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

onMounted(() => {
  loadEmployees()
  try {
    window.addEventListener('updates-changed', loadEmployees)
  } catch {}
})

onBeforeUnmount(() => {
  try {
    window.removeEventListener('updates-changed', loadEmployees)
  } catch {}
})
</script>

<style scoped>
.employee-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-toolbar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 260px;
}

.dept-select {
  width: 200px;
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
</style>
