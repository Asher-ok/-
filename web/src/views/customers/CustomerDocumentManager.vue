<template>
  <div class="customer-document-manager">
    <div class="toolbar">
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        {{ $t('customerDoc.addDocument') }}
      </el-button>
    </div>
    <div class="doc-table-scroll">
      <el-table v-loading="loading" :data="groupedDocuments" row-key="type" table-layout="auto" style="width: 100%" class="doc-table">
        <el-table-column prop="typeLabel" :label="$t('customerDoc.documentType')" width="200" />
        <el-table-column :label="$t('customerDoc.documents')">
          <template #default="{ row }">
            <div v-for="doc in row.items" :key="doc.id" class="doc-row">
              <span class="doc-name">{{ doc.name }}</span>
              <el-tag :type="getStatusTagType(doc.status)" size="small">{{ statusLabel(doc.status) }}</el-tag>
              <el-button-group>
                <el-button size="small" @click="handleEdit(doc)">{{ $t('common.edit') }}</el-button>
                <el-button
                  size="small"
                  :disabled="!doc.file_url && !doc.signed_file_url"
                  @click="handlePreview(doc)"
                >
                  {{ $t('customerDoc.generatePdf') }}
                </el-button>
                <el-button
                  size="small"
                  :disabled="!doc.file_url && !doc.signed_file_url"
                  @click="handleDownload(doc)"
                >
                  {{ $t('common.download') }}
                </el-button>
                <el-button size="small" type="danger" @click="handleDelete(doc)">{{ $t('common.delete') }}</el-button>
              </el-button-group>
            </div>
            <div v-if="!row.items.length" class="no-docs">{{ $t('customerDoc.noDocuments') }}</div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Create document: type + file -->
    <el-dialog v-model="createDialogVisible" :title="$t('customerDoc.addDocument')" width="480px">
      <el-form :model="createForm" :rules="rules" ref="createFormRef" label-width="120px">
        <el-form-item :label="$t('customerDoc.documentType')" prop="document_type">
          <el-select
            v-model="createForm.document_type"
            :placeholder="$t('customerDoc.selectType')"
            style="width: 100%"
          >
            <el-option
              v-for="t in documentTypes"
              :key="t.value"
              :label="$t(t.labelKey)"
              :value="t.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('customerDoc.selectFile')">
          <el-upload
            :auto-upload="false"
            :file-list="createFileList"
            :on-change="handleCreateFileChange"
            :limit="1"
            accept=".pdf,.doc,.docx"
          >
            <el-button type="primary">{{ $t('customerDoc.selectFile') }}</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleCreateSubmit">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- Edit document: dedicated form component per document_type -->
    <el-dialog
      v-model="formEditorVisible"
      :title="formEditorTitle"
      width="90%"
      class="form-editor-dialog"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <component
        v-if="currentEditDoc"
        :is="formComponent"
        ref="formEditorRef"
        :doc="currentEditDoc"
        :customer-id="customerId"
      />
      <template #footer>
        <el-button @click="formEditorVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="formSaving" @click="handleFormEditorSave">
          {{ $t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="previewDialogVisible"
      :title="currentPreviewDoc?.name || $t('common.preview')"
      width="90%"
      top="5vh"
      @close="closePreview"
    >
      <div class="preview-wrapper">
        <div v-if="previewType === 'pdfjs'" ref="previewPdfContainer" class="preview-pdfjs">
          <div ref="previewPdfCanvasWrapper" class="preview-pdfjs-canvases"></div>
        </div>
        <iframe v-else-if="previewUrl" :src="previewUrl" class="preview-iframe"></iframe>
        <div v-else class="preview-loading">{{ $t('common.loading') }}</div>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button v-if="currentPreviewDoc" type="primary" @click="handleDownload(currentPreviewDoc)">
          {{ $t('common.download') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import * as pdfjsDistLegacy from 'pdfjs-dist/legacy/build/pdf.js'
import pdfjsDistLegacyWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min.js?url'
import {
  getDocumentTypes,
  getCustomerDocuments,
  createCustomerDocument,
  updateCustomerDocument,
  deleteCustomerDocument,
  uploadDocumentFile,
  downloadDocument,
  previewDocument,
  syncReviewToRisk
} from '@/api/customerDocuments'
import { getFormComponent } from './document-forms'

defineOptions({ name: 'CustomerDocumentManager' })

const props = defineProps({
  customerId: { type: String, required: true }
})

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))
let pdfjsReady = null
const loadPdfjs = async () => {
  if (pdfjsReady) return pdfjsReady
  pdfjsReady = Promise.resolve().then(() => {
    const lib =
      typeof pdfjsDistLegacy?.getDocument === 'function'
        ? pdfjsDistLegacy
        : typeof pdfjsDistLegacy?.default?.getDocument === 'function'
          ? pdfjsDistLegacy.default
          : pdfjsDistLegacy?.default || pdfjsDistLegacy

    if (typeof lib?.getDocument !== 'function') {
      const topKeys = (Object.keys(pdfjsDistLegacy || {}) || []).slice(0, 12).join(',')
      const defaultKeys = (Object.keys(pdfjsDistLegacy?.default || {}) || []).slice(0, 12).join(',')
      throw new Error(
        `pdfjs load failed: getDocument not found, keys: ${topKeys}${defaultKeys ? `; default keys: ${defaultKeys}` : ''}`
      )
    }

    if (lib?.GlobalWorkerOptions && pdfjsDistLegacyWorkerUrl) {
      lib.GlobalWorkerOptions.workerSrc = pdfjsDistLegacyWorkerUrl
    }

    return lib
  })
  return pdfjsReady
}

const loading = ref(false)
const documents = ref([])
const documentTypes = getDocumentTypes()
const createDialogVisible = ref(false)
const formEditorVisible = ref(false)
const createFormRef = ref(null)
const formEditorRef = ref(null)
const currentEditDoc = ref(null)
const formSaving = ref(false)
const createFileList = ref([])

const previewDialogVisible = ref(false)
const previewType = ref('')
const previewUrl = ref('')
const currentPreviewDoc = ref(null)
const previewBlob = ref(null)
const previewPdfContainer = ref(null)
const previewPdfCanvasWrapper = ref(null)
const previewPdfRenderedKey = ref('')

const createForm = ref({
  document_type: ''
})

const rules = {
  document_type: [{ required: true, message: '请选择文档类型', trigger: 'change' }]
}

const groupedDocuments = computed(() => {
  const groups = {}
  for (const dt of documentTypes) {
    groups[dt.value] = { type: dt.value, typeLabel: t(dt.labelKey), items: [] }
  }
  for (const doc of documents.value) {
    if (groups[doc.document_type]) {
      groups[doc.document_type].items.push(doc)
    }
  }
  return Object.values(groups)
})

const formComponent = computed(() => {
  const type = currentEditDoc.value?.document_type
  return type ? getFormComponent(type) : null
})

const formEditorTitle = computed(() => {
  const doc = currentEditDoc.value
  if (!doc) return ''
  const label = documentTypes.find((dt) => dt.value === doc.document_type)
  const typeLabel = label ? t(label.labelKey) : doc.document_type
  return `${t('customerDoc.editDocument')}: ${doc.name || typeLabel}`
})

function statusLabel(status) {
  if (!status) return '-'
  const map = { draft: 'customerDoc.statusDraft', pending_sign: 'customerDoc.statusPendingSign', signed: 'customerDoc.statusSigned' }
  return t(map[status] || '-')
}

function getStatusTagType(status) {
  const map = { draft: 'info', pending_sign: 'warning', signed: 'success' }
  return map[status] || 'info'
}

function hasFormData(doc) {
  if (!doc?.form_data) return false
  const fd = doc.form_data
  if (typeof fd === 'object') return Object.keys(fd).length > 0
  return !!fd
}

const loadDocuments = async () => {
  loading.value = true
  try {
    documents.value = await getCustomerDocuments(props.customerId)
  } catch (e) {
    ElMessage.error(t('customerDoc.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  createForm.value = { document_type: '' }
  createFileList.value = []
  createDialogVisible.value = true
}

const handleCreateFileChange = (file, fileList) => {
  createFileList.value = fileList
}

const handleCreateSubmit = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const file = createFileList.value.find((f) => f.raw)?.raw
      if (!file) {
        ElMessage.error(t('customerDoc.uploadFailed'))
        return
      }
      const doc = await createCustomerDocument(props.customerId, {
        document_type: createForm.value.document_type,
        name: file.name
      })
      await uploadDocumentFile(props.customerId, doc.id, file)
      ElMessage.success(t('customerDoc.uploadSuccess'))
      createDialogVisible.value = false
      loadDocuments()
    } catch (e) {
      ElMessage.error(e?.response?.data?.detail || e?.message || t('customerDoc.operationFailed'))
    }
  })
}

const handleEdit = (doc) => {
  currentEditDoc.value = doc
  formEditorVisible.value = true
}

const handleFormEditorSave = async () => {
  const editor = formEditorRef.value
  if (!editor || !currentEditDoc.value) return
  formSaving.value = true
  try {
    const data = await editor.validate()
    if (!data) return
    await updateCustomerDocument(props.customerId, currentEditDoc.value.id, {
      name: data.name,
      form_data: data.form_data
    })
    if (currentEditDoc.value.document_type === 'review_form' && data.form_data?.syncToRisk && data.form_data?.goals?.length) {
      try {
        await syncReviewToRisk(props.customerId, currentEditDoc.value.id)
      } catch (syncErr) {
        ElMessage.warning(syncErr.response?.data?.detail || t('customerDoc.syncToRiskFailed'))
      }
    }
    ElMessage.success(t('customerDoc.updateSuccess'))
    formEditorVisible.value = false
    loadDocuments()
  } catch (e) {
    ElMessage.error(e?.message || t('customerDoc.operationFailed'))
  } finally {
    formSaving.value = false
  }
}

const handleDelete = async (doc) => {
  try {
    await ElMessageBox.confirm(t('customerDoc.deleteConfirm'), t('customer.tip'), { type: 'warning' })
    await deleteCustomerDocument(props.customerId, doc.id)
    ElMessage.success(t('customerDoc.deleteSuccess'))
    loadDocuments()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(t('customerDoc.deleteFailed'))
  }
}

const handlePreview = async (doc) => {
  try {
    const blob = await previewDocument(props.customerId, doc.id, 'pdf')
    const mime = (blob?.type || '').toLowerCase()
    const pdfLike = mime.includes('pdf') || mime === 'application/octet-stream' || mime === ''
    if (isMobile.value && pdfLike) {
      currentPreviewDoc.value = doc
      previewType.value = 'pdfjs'
      previewUrl.value = ''
      previewBlob.value = blob
      previewDialogVisible.value = true
      await nextTick()
      await renderPdfInPreviewDialog(blob)
      return
    }

    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 30000)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || t('customerDoc.generatePdfFailed'))
  }
}

const renderPdfInPreviewDialog = async (blob) => {
  if (!previewPdfContainer.value || !previewPdfCanvasWrapper.value) return
  const canvasWrapper = previewPdfCanvasWrapper.value
  const key = `${currentPreviewDoc.value?.id || ''}@@${blob?.size || 0}@@${blob?.type || ''}`
  if (previewPdfRenderedKey.value === key) return
  previewPdfRenderedKey.value = key
  canvasWrapper.innerHTML = ''

  const pdfjs = await loadPdfjs()
  const data = await blob.arrayBuffer()
  const pdf = await pdfjs.getDocument({ data, disableWorker: true }).promise
  const containerWidth = previewPdfContainer.value.clientWidth || 800
  const dpr = Math.min(window.devicePixelRatio || 1, 2.5)

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber)
    const baseViewport = page.getViewport({ scale: 1 })
    const scale = containerWidth / baseViewport.width
    const viewport = page.getViewport({ scale })

    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')
    canvas.width = Math.floor(viewport.width * dpr)
    canvas.height = Math.floor(viewport.height * dpr)
    canvas.style.width = `${Math.floor(viewport.width)}px`
    canvas.style.height = `${Math.floor(viewport.height)}px`
    canvas.style.display = 'block'
    canvas.style.margin = '0 auto 16px'
    canvasWrapper.appendChild(canvas)

    await page.render({
      canvasContext: context,
      viewport,
      transform: [dpr, 0, 0, dpr, 0, 0]
    }).promise
  }
}

const closePreview = () => {
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewDialogVisible.value = false
  previewType.value = ''
  previewUrl.value = ''
  currentPreviewDoc.value = null
  previewBlob.value = null
  previewPdfRenderedKey.value = ''
  if (previewPdfCanvasWrapper.value) {
    previewPdfCanvasWrapper.value.innerHTML = ''
  }
}

const handleDownload = async (doc) => {
  try {
    const res = await downloadDocument(props.customerId, doc.id)
    const blob = res instanceof Blob ? res : res.data
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = doc.name || 'document'
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 3000)
  } catch (e) {
    ElMessage.error(t('customerDoc.downloadFailed'))
  }
}

onMounted(() => {
  loadDocuments()
})
</script>

<style scoped>
.customer-document-manager {
  padding: 10px 0;
}

.toolbar {
  margin-bottom: 16px;
}

.doc-table-scroll {
  width: 100%;
  overflow-x: auto;
}

.doc-table {
  min-width: 860px;
}

.doc-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.doc-row:last-child {
  border-bottom: none;
}

.doc-name {
  flex: 1;
  min-width: 120px;
}

.no-docs {
  color: #909399;
  padding: 12px 0;
}

.form-editor-dialog {
  max-width: 960px;
}

.preview-wrapper {
  height: 70vh;
  overflow: auto;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: 0;
}

.preview-pdfjs {
  width: 100%;
}

.preview-pdfjs-canvases {
  padding: 8px 0;
}

.preview-loading {
  padding: 16px;
  color: #909399;
}
</style>
