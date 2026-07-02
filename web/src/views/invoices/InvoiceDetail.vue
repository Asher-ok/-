<template>
  <div class="invoice-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ $t('invoice.detail') }}</span>
          <div>
            <el-button v-if="invoice.pdf_url" @click="showPreviewDialog = true">{{ $t('invoice.preview') }}</el-button>
            <el-button v-if="invoice.pdf_url && (invoice.status === 'draft' || invoice.status === 'sent')" type="primary" @click="openSendDialog">
              {{ $t('invoice.sendEmail') }}
            </el-button>
            <el-button @click="$router.back()">{{ $t('common.return') }}</el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item :label="$t('invoice.invoiceNumber')">{{ invoice.invoice_number }}</el-descriptions-item>
        <el-descriptions-item :label="$t('invoice.invoiceDate')">{{ formatDate(invoice.invoice_date, 'YYYY-MM-DD') }}</el-descriptions-item>
        <el-descriptions-item :label="$t('invoice.customer')">{{ invoice.customer?.name || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('invoice.customerEmail')">{{ invoice.customer?.email || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('invoice.totalAmount')">${{ invoice.total_amount }}</el-descriptions-item>
        <el-descriptions-item :label="$t('invoice.status')">
          <el-tag :type="getStatusType(invoice.status)">{{ getStatusText(invoice.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('invoice.sentTime')">{{ invoice.sent_at ? formatDate(invoice.sent_at, 'YYYY-MM-DD HH:mm') : '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <el-divider>{{ $t('invoice.invoiceItems') }}</el-divider>
      
      <el-table :data="invoice.items || []" stripe>
        <el-table-column prop="description" :label="$t('invoice.description')" min-width="200" />
        <el-table-column prop="service_code" :label="$t('invoice.serviceCode')" width="150" />
        <el-table-column prop="price" :label="$t('invoice.unitPrice')" width="100">
          <template #default="{ row }">
            ${{ row.price }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" :label="$t('invoice.quantity')" width="100" />
        <el-table-column prop="amount" :label="$t('invoice.amount')" width="100">
          <template #default="{ row }">
            ${{ row.amount }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog v-model="showPreviewDialog" :title="$t('invoice.preview')" width="90%" :close-on-click-modal="false">
      <div v-if="previewUrl" class="pdf-preview-container">
        <iframe :src="previewUrl" class="pdf-iframe" frameborder="0"></iframe>
      </div>
      <div v-else class="pdf-loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>{{ $t('invoice.loading') }}</span>
      </div>
      <template #footer>
        <el-button @click="showPreviewDialog = false">{{ $t('invoice.close') }}</el-button>
        <el-button type="primary" @click="handleDownload">{{ $t('common.download') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="sendLangDialogVisible" :title="$t('invoice.sendEmail')" width="360px">
      <el-form label-width="80px">
        <el-form-item label="语言">
          <el-select v-model="sendLang" style="width: 100%">
            <el-option label="中文" value="zh" />
            <el-option label="English" value="en" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendLangDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="sending" @click="handleSend">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getInvoice, previewInvoice, sendInvoice } from '@/api/invoices'
import { ElMessage } from 'element-plus'
import { formatDate } from '@/utils/formatters'
import { Loading } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import logoDataUrl from '@/assets/logo color.png?inline'

const { t } = useI18n()

const route = useRoute()
const invoiceId = computed(() => route.params.id)
const invoice = ref({})
const loading = ref(false)
const showPreviewDialog = ref(false)
const previewUrl = ref('')
const previewBlob = ref(null)
const sendLangDialogVisible = ref(false)
const sendLang = ref('en')
const sending = ref(false)

const getStatusType = (status) => {
  const map = {
    draft: 'info',
    sent: 'warning',
    paid: 'success'
  }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = {
    draft: t('invoice.draft'),
    sent: t('invoice.sent'),
    paid: t('invoice.paid')
  }
  return map[status] || status
}

const formatCurrency = (val) => {
  const n = Number(val)
  if (val == null || val === '' || isNaN(n)) return '-'
  return `$${n.toFixed(2)}`
}

const formatQty = (val) => {
  const n = Number(val)
  if (val == null || val === '' || isNaN(n)) return '-'
  if (Number.isInteger(n)) return String(n)
  return String(Number(n.toFixed(2))).replace(/\.0+$/, '').replace(/(\.\d*?)0+$/, '$1')
}

const formatDateDDMMYYYY = (val) => {
  if (!val) return ''
  const s = String(val)
  const datePart = s.includes(' ') ? (s.split(' ')[0] || '') : s
  const parts = datePart.split('-')
  if (parts.length !== 3) return datePart
  const [yyyy, mm, dd] = parts
  if (!yyyy || !mm || !dd) return datePart
  return `${dd}/${mm}/${yyyy}`
}

const buildDescriptionLines = (item) => {
  const lines = [item?.description || '-']
  const dateStr = formatDateDDMMYYYY(item?.service_date)
  const start = item?.service_time_start || ''
  const end = item?.service_time_end || ''
  if (dateStr) {
    if (start && end) lines.push(`Date/Time: ${dateStr} ${start}-${end}`)
    else lines.push(`Date/Time: ${dateStr}`)
  }
  return lines
}

const buildInvoicePdfBlob = (invoiceData) => {
  const doc = new jsPDF({ unit: 'pt', format: 'a4' })
  const pageW = doc.internal.pageSize.getWidth()
  const marginX = 50
  let y = 64

  const logoW = 160
  const logoH = 60
  try {
    doc.addImage(logoDataUrl, 'PNG', pageW - marginX - logoW, 56, logoW, logoH)
  } catch (e) {
  }

  doc.setFontSize(30)
  doc.text('TAX INVOICE', pageW / 2, y, { align: 'center' })

  const seller = {
    name: 'EMPOWER HUB',
    abn: '42 679 637 426',
    address: 'UNIT FGL-OFFICE, 1/385 Sherwood Rd, ROCKLEA QLD 4106',
    phone: '0406 888 667',
    email: 'zhaohmei22@hotmail.com'
  }

  y += 44
  doc.setFontSize(12)
  const sellerLines = [
    seller.name,
    `ABN: ${seller.abn}`,
    seller.address,
    `Mobile: ${seller.phone}`,
    `Email: ${seller.email}`
  ]
  sellerLines.forEach((line) => {
    doc.text(line, marginX, y)
    y += 14
  })

  y += 8
  const invoiceNo = invoiceData?.invoice_number || '-'
  const invoiceDate = invoiceData?.invoice_date ? formatDateDDMMYYYY(invoiceData.invoice_date) : '-'
  doc.setFontSize(12)
  doc.text('Invoice Number:', marginX, y)
  doc.text(String(invoiceNo), marginX + 120, y)
  y += 16
  doc.text('Date:', marginX, y)
  doc.text(String(invoiceDate), marginX + 120, y)

  y += 22
  doc.text('TO:', marginX, y)
  doc.text(String(invoiceData?.customer?.name || '-'), marginX + 36, y)
  y += 16
  const ndis = invoiceData?.customer?.ndis_number || ''
  if (ndis) {
    doc.text('NDIS NUMBER:', marginX, y)
    doc.text(String(ndis), marginX + 110, y)
    y += 16
  }

  y += 12

  const items = Array.isArray(invoiceData?.items) ? invoiceData.items : []
  const totalQty = items.reduce((acc, it) => acc + (Number(it?.quantity) || 0), 0)

  autoTable(doc, {
    startY: y,
    theme: 'grid',
    head: [['Description', 'Code', 'Unit Price', 'Amount', 'Amount AUD']],
    body: items.map((it, idx) => [
      buildDescriptionLines(it).join('\n'),
      it?.service_code || '-',
      String(Number(it?.price || 0).toFixed(2)),
      formatQty(it?.quantity),
      String(Number(it?.amount || 0).toFixed(2))
    ]),
    styles: { fontSize: 10, cellPadding: 6, overflow: 'linebreak', lineWidth: 0.6, lineColor: [0, 0, 0], textColor: 0, fillColor: [255, 255, 255] },
    headStyles: { fillColor: [255, 255, 255], textColor: 0, fontStyle: 'bold', lineWidth: 1.2, lineColor: [0, 0, 0] },
    columnStyles: {
      0: { cellWidth: 270 },
      1: { cellWidth: 120 },
      2: { cellWidth: 70, halign: 'right' },
      3: { cellWidth: 50, halign: 'right' },
      4: { cellWidth: 75, halign: 'right' }
    },
    didParseCell: (data) => {
      if (data.section === 'body') {
        if (data.column.index >= 2) data.cell.styles.halign = 'right'
      }
    }
  })

  const finalY = doc.lastAutoTable?.finalY || y
  const total = Number(invoiceData?.total_amount || 0)
  doc.setFontSize(12)
  doc.text('TOTAL', marginX + 270, finalY + 20)
  doc.text(formatQty(totalQty), marginX + 360, finalY + 20, { align: 'right' })
  doc.text(String(total.toFixed(2)), marginX + 500, finalY + 20, { align: 'right' })

  return doc.output('blob')
}

const loadInvoice = async () => {
  if (!invoiceId.value) return
  loading.value = true
  try {
    invoice.value = await getInvoice(invoiceId.value)
  } catch (error) {
    ElMessage.error(t('invoice.loadInvoiceFailed'))
  } finally {
    loading.value = false
  }
}

watch(showPreviewDialog, async (newVal) => {
  if (newVal && invoice.value.pdf_url && invoiceId.value) {
    try {
      const blob = await previewInvoice(invoiceId.value)
      const fileType = blob.type || ''
      const fileUrl = invoice.value.pdf_url || ''
      const isExcel =
        fileType.includes('spreadsheet') ||
        fileType.includes('excel') ||
        fileUrl.endsWith('.xlsx') ||
        fileUrl.endsWith('.xls')

      const nextBlob = isExcel ? buildInvoicePdfBlob(invoice.value) : blob
      previewBlob.value = nextBlob
      previewUrl.value = URL.createObjectURL(nextBlob)
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || t('invoice.previewFailed')
      ElMessage.error(errorMessage)
      showPreviewDialog.value = false
    }
  } else if (!newVal) {
    // 关闭对话框时清理URL
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
    }
    previewUrl.value = ''
    previewBlob.value = null
  }
})

// 监听路由参数变化，确保切换不同发票时能正确加载
watch(() => route.params.id, (newId, oldId) => {
  // 只有当ID真正变化时才重新加载（避免初始化时重复加载）
  if (newId && newId !== oldId && oldId !== undefined) {
    // 重置状态
    invoice.value = {}
    previewUrl.value = ''
    showPreviewDialog.value = false
    // 加载新发票数据
    loadInvoice()
  }
}, { immediate: false })

const getInvoicePreviewBlob = async () => {
  if (previewBlob.value) return previewBlob.value
  const blob = await previewInvoice(invoiceId.value)
  const fileType = blob.type || ''
  const fileUrl = invoice.value.pdf_url || ''
  const isExcel =
    fileType.includes('spreadsheet') ||
    fileType.includes('excel') ||
    fileUrl.endsWith('.xlsx') ||
    fileUrl.endsWith('.xls')
  const nextBlob = isExcel ? buildInvoicePdfBlob(invoice.value) : blob
  previewBlob.value = nextBlob
  return nextBlob
}

const saveBlobToLocal = async (blob, suggestedName) => {
  const picker = window?.showSaveFilePicker
  if (typeof picker === 'function') {
    try {
      const handle = await picker({
        suggestedName,
        types: [
          {
            description: 'PDF',
            accept: { 'application/pdf': ['.pdf'] }
          }
        ]
      })
      const writable = await handle.createWritable()
      await writable.write(blob)
      await writable.close()
      return
    } catch (e) {
      const name = e?.name || ''
      if (name === 'AbortError') return
    }
  }

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = suggestedName
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

const handleDownload = async () => {
  if (!invoice.value.pdf_url || !invoiceId.value) {
    ElMessage.warning(t('invoice.fileNotExists'))
    return
  }
  try {
    const nextBlob = await getInvoicePreviewBlob()
    const invoiceNo = invoice.value.invoice_number || invoiceId.value
    await saveBlobToLocal(nextBlob, `${invoiceNo}.pdf`)
  } catch (error) {
    const errorMessage = error.response?.data?.detail || error.message || t('invoice.downloadFailed')
    ElMessage.error(errorMessage)
  }
}

const handleSend = async () => {
  if (!invoiceId.value) return
  sending.value = true
  try {
    const res = await sendInvoice(invoiceId.value, sendLang.value)
    const payload = res?.data ?? res
    const sentEmail = payload?.email ?? payload?.data?.email ?? payload?.result?.email ?? ''
    if (sentEmail) {
      ElMessage.success(`${t('invoice.invoiceSentSuccess')} ${sentEmail}`)
    } else {
      ElMessage.success(t('invoice.sendSuccess'))
    }
    loadInvoice()
    sendLangDialogVisible.value = false
  } catch (error) {
    const errorMessage = error.response?.data?.detail || error.message || t('invoice.sendFailed')
    ElMessage.error(errorMessage)
  } finally {
    sending.value = false
  }
}

const openSendDialog = () => {
  sendLang.value = 'en'
  sendLangDialogVisible.value = true
}

onMounted(() => {
  // 确保初始化时预览对话框是关闭的
  showPreviewDialog.value = false
  previewUrl.value = ''
  // 只在有发票ID时加载
  if (invoiceId.value) {
  loadInvoice()
  }
})
</script>

<style scoped>
.invoice-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pdf-preview-container {
  width: 100%;
  height: 70vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.pdf-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 70vh;
  flex-direction: column;
  gap: 10px;
  color: #909399;
}

</style>
