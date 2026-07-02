<template>
  <div class="unissued-invoice-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('invoice.unissuedTab') || '未开发票' }}</span>
        </div>
      </template>
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="title" :label="$t('task.title')" min-width="180" />
        <el-table-column :label="$t('invoice.customer')" min-width="140">
          <template #default="{ row }">
            <span>{{ row.customer?.name || row.customer_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('task.assignedEmployeeLabel')" min-width="160">
          <template #default="{ row }">
            <span>{{ row.assigned_employee?.name || row.assigned_employee_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('task.serviceItem')" min-width="160">
          <template #default="{ row }">
            <span>{{ getServiceCodeText(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('invoice.totalAmount')" width="140">
          <template #default="{ row }">
            <span>${{ formatAmountNumber(getTaskTotalAmount(row)) }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('invoice.operations')" width="180" :fixed="isMobile ? false : 'right'">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="openGenerate(row)">{{ $t('invoice.generateInvoice') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showDialog" :title="$t('invoice.generateInvoice')" width="900px" :close-on-click-modal="false">
      <div class="preview-area" v-loading="previewLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('invoice.customer')">{{ preview.customerName }}</el-descriptions-item>
          <el-descriptions-item :label="$t('task.assignedEmployeeLabel')">{{ preview.employeeName }}</el-descriptions-item>
          <el-descriptions-item :label="$t('invoice.invoiceDate')">{{ preview.invoiceDate }}</el-descriptions-item>
          <el-descriptions-item :label="$t('invoice.totalAmount')">${{ formatAmountNumber(preview.totalAmount) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>{{ $t('invoice.invoiceItems') }}</el-divider>
        <el-table :data="preview.items" stripe>
          <el-table-column :label="$t('invoice.description')" min-width="180">
            <template #default="{ row }">
              <span>{{ row.description }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceCode')" min-width="140">
            <template #default="{ row }">
              <span>{{ row.service_code || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.unitPrice')" width="120">
            <template #default="{ row }">
              <span>${{ formatAmountNumber(row.price) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceDuration')" width="120">
            <template #default="{ row }">
              <span>{{ row.quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.totalPrice')" width="120">
            <template #default="{ row }">
              <span class="item-amount">${{ formatAmountNumber(row.amount != null ? row.amount : row.price * row.quantity) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('task.serviceStartTime')" width="180">
            <template #default="{ row }">
              <span>{{ formatDateTimeToMinute(row.service_time_start) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('task.serviceEndTime')" width="180">
            <template #default="{ row }">
              <span>{{ formatDateTimeToMinute(row.service_time_end) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="showDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="generating" @click="confirmGenerate">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({
  name: 'UnissuedInvoices'
})
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getTasksForInvoice, getInvoiceTaskDetail, generateInvoiceForTask, updateInvoice } from '@/api/invoices'
import { getTasks } from '@/api/tasks'
import { formatDateTimeToMinute } from '@/utils/formatters'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))
const router = useRouter()

const tasks = ref([])
const loading = ref(false)
const showDialog = ref(false)
const previewLoading = ref(false)
const generating = ref(false)
const currentTask = ref(null)
const preview = ref({
  customerId: '',
  customerName: '',
  employeeId: '',
  employeeName: '',
  invoiceDate: '',
  items: [],
  totalAmount: 0
})

const formatAmountNumber = (num) => {
  const n = Number(num || 0)
  return n.toFixed(2)
}

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

const getRowTaskId = (row) => {
  return row?.task_id || row?.taskId || row?.id || ''
}

const getServiceCodeText = (row) => {
  const rawList = Array.isArray(row?.services) ? row.services : (Array.isArray(row?.service_items) ? row.service_items : [])
  const list = rawList.map((s) => s?.service_code || s?.code || '').filter(Boolean)
  return list.length ? list.join(', ') : row?.service_code || '-'
}

const getTaskTotalAmount = (row) => {
  const direct = row?.total_amount != null ? Number(row.total_amount) : null
  if (direct != null && !isNaN(direct)) return direct
  const list = Array.isArray(row?.services) ? row.services : (Array.isArray(row?.service_items) ? row.service_items : [])
  if (!list.length) return Number(row?.total_price || 0) || 0
  return list.reduce((sum, s) => {
    const p = Number(s?.total_price != null ? s.total_price : (Number(s?.unit_price || 0) * Number(s?.duration_hours || 0)))
    return sum + (isNaN(p) ? 0 : p)
  }, 0)
}

const normalizeServiceLine = (line, idx = 0) => {
  const unitRaw = line?.unit_price_override ?? line?.unit_price ?? line?.price ?? line?.unitPrice ?? null
  const qtyRaw =
    line?.quantity ??
    line?.duration_hours ??
    line?.service_duration_hours ??
    line?.duration ??
    line?.hours ??
    null
  const amountRaw =
    line?.amount ??
    line?.total_price ??
    line?.total_amount ??
    line?.line_total ??
    line?.total ??
    null

  const unitPrice = unitRaw != null && !isNaN(Number(unitRaw)) ? Number(unitRaw) : 0
  const quantity = qtyRaw != null && !isNaN(Number(qtyRaw)) ? Number(qtyRaw) : 0
  const amountDirect = amountRaw != null && !isNaN(Number(amountRaw)) ? Number(amountRaw) : null
  const amountDerived = Number((unitPrice * quantity).toFixed(2))

  const start = line?.service_time_start || line?.service_start_time || line?.serviceTimeStart || ''
  const end = line?.service_time_end || line?.service_end_time || line?.serviceTimeEnd || ''

  return {
    id: line?.id ?? `line_${idx}`,
    description:
      line?.description ||
      line?.remark ||
      line?.service_name ||
      line?.name ||
      line?.level3_name ||
      line?.level2_name ||
      line?.level1_name ||
      '',
    service_code: line?.service_code || line?.code || line?.serviceCode || '',
    price: unitPrice,
    quantity,
    amount: amountDirect != null ? amountDirect : amountDerived,
    service_time_start: start === '0000' ? '' : start,
    service_time_end: end === '0000' ? '' : end
  }
}

const normalizeInvoiceTaskDetail = (detail) => {
  const payload = detail?.data ?? detail
  const task = payload?.task || null
  const customer = payload?.customer || null
  const employee = payload?.employee || payload?.assigned_employee || null
  const serviceLinesRaw =
    payload?.service_lines || payload?.serviceLines || payload?.services || payload?.service_items || []
  const serviceLines = Array.isArray(serviceLinesRaw) ? serviceLinesRaw : []
  const items = serviceLines.map((l, idx) => normalizeServiceLine(l, idx))
  const total = items.reduce((sum, it) => sum + Number(it.amount || 0), 0)
  return { task, customer, employee, items, total_amount: Number(total.toFixed(2)) }
}

const loadTasks = async () => {
  loading.value = true
  try {
    const rows = await getTasksForInvoice()
    const list = getArrayFromResponse(rows)
    if (list.length) {
      tasks.value = list.map((r) => ({
        ...r,
        id: r?.id ?? r?.task_id ?? r?.taskId
      }))
    } else {
      const fallback = await getTasks({ status: 'approved' })
      tasks.value = getArrayFromResponse(fallback).map((r) => ({
        ...r,
        id: r?.id ?? r?.task_id ?? r?.taskId
      }))
    }
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

const openGenerate = async (task) => {
  const tid = getRowTaskId(task)
  if (!tid) return
  currentTask.value = { ...task, id: tid }
  const cid = task.customer_id || task.customer?.id || ''
  const cname = task.customer?.name || task.customer_name || ''
  const eid = task.assigned_employee_id || task.assigned_employee?.id || ''
  const ename = task.assigned_employee?.name || task.assigned_employee_name || ''
  preview.value.customerId = cid
  preview.value.customerName = cname || '-'
  preview.value.employeeId = eid
  preview.value.employeeName = ename || '-'
  preview.value.invoiceDate = new Date().toISOString().split('T')[0]
  showDialog.value = true

  previewLoading.value = true
  try {
    const detail = await getInvoiceTaskDetail(tid)
    const normalized = normalizeInvoiceTaskDetail(detail)
    const finalCustomerName = normalized.customer?.name || preview.value.customerName || '-'
    const finalEmployeeName =
      normalized.employee?.name ||
      preview.value.employeeName ||
      '-'
    preview.value.customerName = finalCustomerName
    preview.value.employeeName = finalEmployeeName
    preview.value.items = normalized.items.map((it) => ({
      ...it,
      description: it.description || task.title || task.id
    }))
    preview.value.totalAmount = normalized.total_amount
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('invoice.generateFailed'))
    showDialog.value = false
  } finally {
    previewLoading.value = false
  }
}

const confirmGenerate = async () => {
  if (!currentTask.value?.id) return
  try {
    generating.value = true
    const taskId = currentTask.value.id
    const fmtDate = (s) => {
      if (!s || typeof s !== 'string') return ''
      const parts = s.split(' ')
      return parts[0] || ''
    }
    const fmtHHmm = (s) => {
      if (!s || typeof s !== 'string') return ''
      if (s.length === 4 && /^\d{4}$/.test(s)) return s
      const t = s.includes(' ') ? s.split(' ')[1] || '' : s
      const hh = t.slice(0, 2)
      const mm = t.slice(3, 5)
      return hh && mm ? `${hh}${mm}` : ''
    }
    const items = Array.isArray(preview.value.items) ? preview.value.items : []
    const payload = {
      customer_id: preview.value.customerId || null,
      employee_id: preview.value.employeeId || null,
      invoice_date: preview.value.invoiceDate,
      items: items.map((it) => {
        const unit = it?.price != null ? Number(it.price) : (it?.unit_price != null ? Number(it.unit_price) : 0)
        const qty = it?.quantity != null ? Number(it.quantity) : (it?.duration_hours != null ? Number(it.duration_hours) : 0)
        const amt = it?.amount != null ? Number(it.amount) : Number((unit * qty).toFixed(2))
        return {
          task_service_item_id: it?.task_service_item_id || it?.id || null,
          description: it?.description || currentTask.value.title || currentTask.value.id || '',
          code: it?.service_code || it?.code || '',
          unit_price: unit,
          quantity: qty,
          amount: amt,
          service_date: it?.service_date || fmtDate(it?.service_time_start || ''),
          service_time_start: fmtHHmm(it?.service_time_start || ''),
          service_time_end: fmtHHmm(it?.service_time_end || '')
        }
      })
    }
    const res = await generateInvoiceForTask(taskId, payload)
    ElMessage.success(t('invoice.generateSuccess'))
    showDialog.value = false
    await loadTasks()
    const id = res?.id || res?.invoice_id || res?.invoiceId
    if (id) {
      try {
        const detail = await getInvoiceTaskDetail(taskId)
        const normalized = normalizeInvoiceTaskDetail(detail)
        const toItems = (normalized.items || []).map((it) => {
          const start = it?.service_time_start || ''
          const end = it?.service_time_end || ''
          const datePart = start && typeof start === 'string' ? (start.split(' ')[0] || '') : ''
          const hhmm = (s) => {
            if (!s || typeof s !== 'string') return ''
            if (/^\d{4}$/.test(s)) return s
            const t = s.includes(' ') ? s.split(' ')[1] || '' : s
            const hh = t.slice(0, 2)
            const mm = t.slice(3, 5)
            return hh && mm ? `${hh}${mm}` : ''
          }
          const price = Number(it?.price != null ? it.price : (it?.unit_price || 0))
          const qty = Number(it?.quantity != null ? it.quantity : (it?.duration_hours || 0))
          const amount = Number(it?.amount != null ? it.amount : Number((price * qty).toFixed(2)))
          return {
            task_id: taskId,
            description: it?.description || currentTask.value.title || currentTask.value.id || '',
            service_code: it?.service_code || it?.code || '',
            price,
            quantity: qty,
            service_date: datePart,
            service_time_start: hhmm(start),
            service_time_end: hhmm(end),
            amount
          }
        })
        await updateInvoice(id, {
          customer_id: preview.value.customerId || null,
          invoice_date: `${preview.value.invoiceDate}T00:00:00.000Z`,
          items: toItems
        })
      } catch {}
      router.push(`/invoices/${id}`)
    }
    currentTask.value = null
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('invoice.generateFailed'))
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.unissued-invoice-list {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.item-amount {
  font-weight: 600;
}
</style>
