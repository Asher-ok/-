<template>
  <div class="leave-list">
    <el-card>
      <template #header>
        <span>{{ $t('leave.title') }}</span>
      </template>
      <el-table
        :data="sortedItems"
        v-loading="loading"
        stripe
        :default-sort="{ prop: 'start_date', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="employee_name" :label="$t('leave.employeeName')" width="170">
          <template #default="{ row }">
            <span class="clickable-with-dot">
              <span v-if="row.has_update" class="row-dot" />
              <span>{{ row.employee_name || '-' }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="start_date" column-key="start_date" :label="$t('leave.startDate')" width="230" sortable="custom" />
        <el-table-column prop="end_date" column-key="end_date" :label="$t('leave.endDate')" width="230" sortable="custom" />
        <el-table-column prop="reason" :label="$t('leave.reason')" min-width="320" show-overflow-tooltip />
        <el-table-column prop="status" :label="$t('leave.status')" width="140">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operations')" width="220" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <div class="action-buttons">
                <el-button type="success" size="small" @click="handleApprove(row)">{{ $t('leave.approve') }}</el-button>
                <el-button type="danger" size="small" @click="handleReject(row)">{{ $t('leave.reject') }}</el-button>
              </div>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, computed, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getLeaveRequests, approveLeave, rejectLeave } from '@/api/leaveRequests'
import { markUpdatesRead } from '@/api/updates'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))
const loading = ref(false)
const items = ref([])
const sortState = reactive({
  prop: 'start_date',
  order: 'descending'
})

function statusLabel(s) {
  const map = { pending: t('leave.pending'), approved: t('leave.approved'), rejected: t('leave.rejected') }
  return map[s] || s
}

const load = async () => {
  loading.value = true
  try {
    items.value = await getLeaveRequests() || []
  } catch {
    ElMessage.error(t('leave.loadFailed'))
  } finally {
    loading.value = false
  }
}

const toTime = (value) => {
  const ms = new Date(value || '').getTime()
  return Number.isFinite(ms) ? ms : 0
}

const sortedItems = computed(() => {
  const list = Array.isArray(items.value) ? [...items.value] : []
  const { prop, order } = sortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'start_date' || prop === 'end_date') {
    return list.sort((a, b) => (toTime(a?.[prop]) - toTime(b?.[prop])) * dir)
  }
  return list
})

const handleSortChange = ({ prop, order }) => {
  sortState.prop = prop || ''
  sortState.order = order
}

const handleApprove = async (row) => {
  try {
    await approveLeave(row.id)
    ElMessage.success(t('leave.approveSuccess'))
    load()
  } catch {
    ElMessage.error(t('leave.operationFailed'))
  }
}

const handleReject = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt(t('leave.rejectReasonPrompt'), t('leave.reject'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel')
    })
    await rejectLeave(row.id, value)
    ElMessage.success(t('leave.rejectSuccess'))
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(t('leave.operationFailed'))
  }
}

onMounted(async () => {
  await load()
  markUpdatesRead('leave_request')
    .then(() => {
      items.value = (items.value || []).map((i) => ({ ...i, has_update: false }))
    })
    .catch(() => {})
})
</script>

<style scoped>
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
