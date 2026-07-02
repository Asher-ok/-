<template>
  <div class="ndis-report-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('ndisReport.title') }}</span>
        </div>
      </template>

      <el-form :model="form" label-width="140px" class="report-form">
        <el-form-item :label="$t('ndisReport.reportType')">
          <el-radio-group v-model="form.reportType">
            <el-radio value="service-usage">{{ $t('ndisReport.serviceUsage') }}</el-radio>
            <el-radio value="financial">{{ $t('ndisReport.financial') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="$t('ndisReport.customer')">
          <el-select
            v-model="form.customer_id"
            :placeholder="$t('ndisReport.selectCustomer')"
            clearable
            filterable
            style="width: 320px"
          >
            <el-option
              v-for="c in customerOptions"
              :key="c.id"
              :label="`${c.name}${c.customer_type === 'NDIS' && c.ndis_number ? ' (' + c.ndis_number + ')' : ''}`"
              :value="c.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('ndisReport.dateRange')">
          <el-date-picker
            v-model="form.dateRange"
            type="daterange"
            range-separator="-"
            :start-placeholder="$t('ndisReport.dateStart')"
            :end-placeholder="$t('ndisReport.dateEnd')"
            value-format="YYYY-MM-DD"
            style="width: 320px"
          />
        </el-form-item>
        <el-form-item :label="$t('ndisReport.ndisOnly')">
          <el-checkbox v-model="form.ndisOnly">{{ $t('ndisReport.ndisOnlyLabel') }}</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="querying" @click="handleQuery">
            <el-icon><Search /></el-icon>
            {{ $t('ndisReport.query') }}
          </el-button>
          <el-button type="success" :loading="downloading" @click="handleDownload">
            <el-icon><Download /></el-icon>
            {{ $t('ndisReport.download') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="tableData.length > 0 || hasQueried" class="table-card">
      <template #header>
        <span>{{ form.reportType === 'service-usage' ? $t('ndisReport.serviceUsage') : $t('ndisReport.financial') }}</span>
      </template>
      <el-table
        :data="tableData"
        v-loading="querying"
        stripe
        border
        style="width: 100%"
        show-summary
        :summary-method="getSummaryMethod"
      >
        <template v-if="form.reportType === 'service-usage'">
          <el-table-column prop="date" :label="$t('ndisReport.colDate')" width="110" />
          <el-table-column prop="participant" :label="$t('ndisReport.colParticipant')" min-width="120" />
          <el-table-column prop="ndis_number" :label="$t('ndisReport.colNdisNumber')" width="130" />
          <el-table-column prop="service_item" :label="$t('ndisReport.colServiceItem')" min-width="140" />
          <el-table-column prop="hours" :label="$t('ndisReport.colHours')" width="80" />
          <el-table-column prop="staff" :label="$t('ndisReport.colStaff')" min-width="100" />
          <el-table-column prop="cost" :label="$t('ndisReport.colCost')" width="100" align="right">
            <template #default="{ row }">
              {{ formatCost(row.cost) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" :label="$t('ndisReport.colStatus')" width="90" />
        </template>
        <template v-else>
          <el-table-column prop="invoice_number" :label="$t('ndisReport.colInvoiceNo')" width="130" />
          <el-table-column prop="date" :label="$t('ndisReport.colDate')" width="110" />
          <el-table-column prop="participant" :label="$t('ndisReport.colParticipant')" min-width="120" />
          <el-table-column prop="ndis_number" :label="$t('ndisReport.colNdisNumber')" width="130" />
          <el-table-column prop="total_amount" :label="$t('ndisReport.colTotalAmount')" width="110" align="right">
            <template #default="{ row }">
              {{ formatCost(row.total_amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" :label="$t('ndisReport.colStatus')" width="90" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
defineOptions({ name: 'NdisReportPage' })
import { ref, reactive, computed, onMounted, watch } from 'vue'
import {
  downloadServiceUsageReport,
  downloadFinancialReport,
  getServiceUsageData,
  getFinancialData
} from '@/api/ndisReports'
import { getCustomers } from '@/api/customers'
import { ElMessage } from 'element-plus'
import { Download, Search } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const customers = ref([])
const downloading = ref(false)
const querying = ref(false)
const tableData = ref([])
const summary = ref(null)
const hasQueried = ref(false)

const form = reactive({
  reportType: 'service-usage',
  customer_id: '',
  dateRange: null,
  ndisOnly: true
})

const customerOptions = computed(() => customers.value)

const getParams = () => ({
  customer_id: form.customer_id || undefined,
  date_start: form.dateRange?.[0] || undefined,
  date_end: form.dateRange?.[1] || undefined,
  ndis_only: form.ndisOnly
})

const formatCost = (val) => {
  if (val == null || val === '') return '-'
  const n = Number(val)
  return isNaN(n) ? '-' : `$${n.toFixed(2)}`
}

const handleQuery = async () => {
  querying.value = true
  hasQueried.value = true
  try {
    const params = getParams()
    const fn = form.reportType === 'service-usage' ? getServiceUsageData : getFinancialData
    const res = await fn(params)
    tableData.value = res.data?.rows || []
    summary.value = res.data?.summary || null
  } catch (e) {
    ElMessage.error(t('ndisReport.queryFailed') + ': ' + (e.response?.data?.detail || e.message))
    tableData.value = []
    summary.value = null
  } finally {
    querying.value = false
  }
}

const getSummaryMethod = ({ columns }) => {
  if (!summary.value) return []
  const sums = []
  columns.forEach((col) => {
    if (col.property === 'date' || col.property === 'invoice_number') {
      sums.push(t('ndisReport.summaryLabel'))
    } else if (form.reportType === 'service-usage') {
      if (col.property === 'hours') sums.push(summary.value.total_hours)
      else if (col.property === 'cost') sums.push(formatCost(summary.value.total_cost))
      else sums.push('')
    } else {
      if (col.property === 'total_amount') sums.push(formatCost(summary.value.total_amount))
      else sums.push('')
    }
  })
  return sums
}

const loadCustomers = async () => {
  try {
    customers.value = await getCustomers()
  } catch (e) {
    ElMessage.error(t('ndisReport.loadCustomersFailed'))
  }
}

const handleDownload = async () => {
  downloading.value = true
  try {
    const params = getParams()
    const fn = form.reportType === 'service-usage' ? downloadServiceUsageReport : downloadFinancialReport
    const response = await fn(params)
    const blob = response instanceof Blob ? response : response.data
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const suffix = form.reportType === 'service-usage' ? 'Service_Usage' : 'Financial'
    link.download = `NDIS_${suffix}_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 3000)
    ElMessage.success(t('ndisReport.downloadSuccess'))
  } catch (e) {
    ElMessage.error(t('ndisReport.downloadFailed') + ': ' + (e.response?.data?.detail || e.message))
  } finally {
    downloading.value = false
  }
}

watch(() => form.reportType, () => {
  tableData.value = []
  summary.value = null
})

onMounted(() => {
  loadCustomers()
})
</script>

<style scoped>
.ndis-report-page {
  padding: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.report-form {
  max-width: 480px;
}
.table-card {
  margin-top: 16px;
}
</style>
