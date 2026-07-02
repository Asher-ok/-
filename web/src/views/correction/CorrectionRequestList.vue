<template>
  <div class="correction-list">
    <el-card>
      <template #header>
        <span>{{ $t('correction.title') }}</span>
      </template>
      <el-table :data="items" v-loading="loading" stripe>
        <el-table-column prop="task_id" :label="$t('correction.taskId')" width="200" />
        <el-table-column prop="reason" :label="$t('correction.reason')" />
        <el-table-column prop="employee_note" :label="$t('correction.employeeNote')" min-width="180" />
        <el-table-column :label="$t('correction.services')" min-width="220">
          <template #default="{ row }">
            <span>{{ serviceSummary(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('correction.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operations')" width="240" :fixed="isMobile ? false : 'right'">
          <template #default="{ row }">
            <el-button size="small" @click="handleViewTask(row)">{{ $t('correction.viewTask') }}</el-button>
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(row)">{{ $t('correction.approve') }}</el-button>
              <el-button type="danger" size="small" @click="handleReject(row)">{{ $t('correction.reject') }}</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { getCorrectionRequests, approveCorrection, rejectCorrection } from '@/api/correctionRequests'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))
const router = useRouter()
const loading = ref(false)
const items = ref([])

function statusLabel(s) {
  const map = { pending: t('correction.pending'), approved: t('correction.approved'), rejected: t('correction.rejected') }
  return map[s] || s
}

function serviceSummary(row) {
  const list = Array.isArray(row?.services) ? row.services : []
  if (!list.length) return '-'
  const codes = list
    .map((s) => s?.service_code || s?.code || '')
    .filter(Boolean)
    .slice(0, 3)
  const prefix = codes.length ? codes.join(', ') : `${list.length}`
  return list.length > 3 ? `${prefix}…` : prefix
}

const normalizeArray = (res) => {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.items)) return res.items
  if (Array.isArray(res?.rows)) return res.rows
  if (Array.isArray(res?.data)) return res.data
  return []
}

const load = async () => {
  loading.value = true
  try {
    const res = await getCorrectionRequests()
    items.value = normalizeArray(res)
  } catch {
    ElMessage.error(t('correction.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleViewTask = (row) => {
  if (!row?.task_id) return
  router.push(`/tasks/${row.task_id}`)
}

const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(t('correction.approveConfirm'), t('task.tip'), { type: 'warning' })
    await approveCorrection(row.id)
    ElMessage.success(t('correction.approveSuccess'))
    load()
  } catch {
    ElMessage.error(t('correction.operationFailed'))
  }
}

const handleReject = async (row) => {
  try {
    await ElMessageBox.confirm(t('correction.rejectConfirm'), t('task.tip'), { type: 'warning' })
    await rejectCorrection(row.id)
    ElMessage.success(t('correction.rejectSuccess'))
    load()
  } catch {
    ElMessage.error(t('correction.operationFailed'))
  }
}

onMounted(load)
</script>
