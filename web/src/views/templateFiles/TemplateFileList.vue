<template>
  <div class="template-file-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ $t('templateFiles.title') }}</span>
          <div class="header-actions">
            <el-button type="primary" @click="openCreateDialog">
              <el-icon><Plus /></el-icon>
              {{ $t('templateFiles.add') }}
            </el-button>
            <el-button @click="load">
              <el-icon><Refresh /></el-icon>
              {{ $t('common.refresh') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="table-scroll">
        <el-table
          :data="sortedRows"
          v-loading="loading"
          stripe
          table-layout="auto"
          :default-sort="{ prop: 'created_at', order: 'descending' }"
          @sort-change="handleSortChange"
        >
          <el-table-column prop="template_name" :label="$t('templateFiles.templateName')" min-width="220" />
          <el-table-column prop="file_name" :label="$t('templateFiles.fileName')" min-width="260">
            <template #default="{ row }">
              <el-link type="primary" :underline="true" @click="openPreview(row)">
                {{ row.file_name || '-' }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="file_type" :label="$t('templateFiles.fileType')" width="110" />
          <el-table-column prop="created_at" column-key="created_at" :label="$t('templateFiles.createdAt')" width="200" sortable="custom" />
          <el-table-column :label="$t('templateFiles.placeholders')" width="120" align="center">
            <template #default="{ row }">
              <el-button size="small" @click="openPlaceholders(row)">{{ $t('templateFiles.placeholders') }}</el-button>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.operations')" width="260" align="right" header-align="left" :fixed="isMobile ? false : 'right'">
            <template #default="{ row }">
              <div class="op-row">
                <el-upload
                  :show-file-list="false"
                  :auto-upload="false"
                  accept=".pdf,.doc,.docx"
                  :on-change="(file) => reupload(row, file)"
                >
                  <el-button size="small">{{ $t('common.reupload') }}</el-button>
                </el-upload>
                <el-button size="small" @click="download(row)">{{ $t('common.download') }}</el-button>
                <el-button size="small" type="danger" @click="remove(row)">{{ $t('common.delete') }}</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-dialog v-model="createDialogVisible" :title="$t('templateFiles.add')" width="520px">
      <el-form label-width="100px">
        <el-form-item :label="$t('templateFiles.templateName')">
          <el-input v-model="createForm.templateName" />
        </el-form-item>
        <el-form-item :label="$t('common.selectFile')">
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".pdf,.doc,.docx"
            :file-list="createFileList"
            :on-change="handleCreateFileChange"
            :on-remove="() => (createFileList = [])"
          >
            <el-button type="primary">{{ $t('common.selectFile') }}</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!canCreate" :loading="creating" @click="create">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="placeholderDialogVisible" :title="$t('templateFiles.placeholders')" width="520px">
      <el-table :data="placeholderRows" stripe>
        <el-table-column prop="key" :label="$t('templateFiles.placeholderKey')" />
      </el-table>
      <template #footer>
        <el-button @click="placeholderDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewDialogVisible" :title="currentPreviewRow?.file_name || $t('common.preview')" width="90%" top="5vh" @close="closePreview">
      <div class="preview-wrapper">
        <div
          v-if="previewType === 'pdfjs'"
          ref="previewPdfContainer"
          class="preview-pdfjs"
        >
          <div ref="previewPdfCanvasWrapper" class="preview-pdfjs-canvases"></div>
        </div>
        <iframe v-else-if="previewUrl" :src="previewUrl" class="preview-iframe"></iframe>
        <div v-else-if="previewError" class="preview-unsupported">
          <p>{{ previewError }}</p>
        </div>
        <div v-else class="preview-loading">
          <span>{{ $t('common.loading') }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button v-if="currentPreviewRow" type="primary" @click="download(currentPreviewRow)">
          {{ $t('common.download') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'TemplateFiles' })
import { ref, computed, onMounted, inject, nextTick, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import * as pdfjsDistLegacy from 'pdfjs-dist/legacy/build/pdf.js'
import pdfjsDistLegacyWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min.js?url'
import {
  getTemplateFiles,
  createTemplateFile,
  updateTemplateFile,
  deleteTemplateFile,
  getTemplateFilePlaceholders,
  previewTemplateFile,
  downloadTemplateFile
} from '@/api/templateFiles'

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

const rows = ref([])
const loading = ref(false)
const sortState = reactive({
  prop: 'created_at',
  order: 'descending'
})

const createDialogVisible = ref(false)
const createForm = ref({ templateName: '' })
const createFileList = ref([])
const creating = ref(false)

const placeholderDialogVisible = ref(false)
const placeholderRows = ref([])

const previewDialogVisible = ref(false)
const previewUrl = ref('')
const currentPreviewRow = ref(null)
const previewError = ref('')
const previewType = ref('')
const previewBlob = ref(null)
const previewPdfContainer = ref(null)
const previewPdfCanvasWrapper = ref(null)
const previewPdfRenderedKey = ref('')

const canCreate = computed(() => {
  return (createForm.value.templateName || '').trim().length > 0 && createFileList.value.length > 0
})

const toTime = (value) => {
  const ms = new Date(value || '').getTime()
  return Number.isFinite(ms) ? ms : 0
}

const sortedRows = computed(() => {
  const list = Array.isArray(rows.value) ? [...rows.value] : []
  const { prop, order } = sortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'created_at') {
    return list.sort((a, b) => (toTime(a?.created_at) - toTime(b?.created_at)) * dir)
  }
  return list
})

const handleSortChange = ({ prop, order }) => {
  sortState.prop = prop || ''
  sortState.order = order
}

const load = async () => {
  loading.value = true
  try {
    const res = await getTemplateFiles()
    rows.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  createForm.value = { templateName: '' }
  createFileList.value = []
  createDialogVisible.value = true
}

const handleCreateFileChange = (file, fileList) => {
  createFileList.value = fileList.slice(-1)
}

const create = async () => {
  const name = (createForm.value.templateName || '').trim()
  const file = createFileList.value.find((f) => f.raw)?.raw
  if (!name || !file) return
  creating.value = true
  try {
    await createTemplateFile(name, file)
    ElMessage.success('创建成功')
    createDialogVisible.value = false
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

const reupload = async (row, uploadFile) => {
  const file = uploadFile?.raw
  if (!file) return
  try {
    await updateTemplateFile(row.id, { file })
    ElMessage.success('更新成功')
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '更新失败')
  }
}

const remove = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除模板「${row.template_name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteTemplateFile(row.id)
    ElMessage.success('删除成功')
    await load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '删除失败')
  }
}

const openPlaceholders = async (row) => {
  try {
    const res = await getTemplateFilePlaceholders(row.id)
    const list = res?.placeholders || []
    placeholderRows.value = list.map((key) => ({ key }))
    placeholderDialogVisible.value = true
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '获取失败')
  }
}

const openPreview = async (row) => {
  closePreview()
  currentPreviewRow.value = row
  previewDialogVisible.value = true
  previewError.value = ''
  try {
    const ext = (row.file_type || '').toString().toLowerCase()
    if (!['pdf', 'doc', 'docx'].includes(ext)) {
      previewError.value = t('templateFiles.previewUnsupported')
      return
    }
    const blob = await previewTemplateFile(row.id, 'pdf')
    const mime = (blob?.type || '').toLowerCase()
    const pdfLike = mime.includes('pdf') || mime === 'application/octet-stream' || mime === '' || ext === 'pdf'
    if (isMobile.value && pdfLike) {
      previewType.value = 'pdfjs'
      previewUrl.value = ''
      previewBlob.value = blob
      await nextTick()
      await renderPdfInPreviewDialog(blob)
    } else {
      previewType.value = 'iframe'
      previewBlob.value = null
      previewUrl.value = URL.createObjectURL(blob)
    }
  } catch (e) {
    previewError.value = e?.response?.data?.detail || e?.message || t('templateFiles.previewUnsupported')
    ElMessage.error(previewError.value)
  }
}

const renderPdfInPreviewDialog = async (blob) => {
  if (!previewPdfContainer.value || !previewPdfCanvasWrapper.value) return
  const canvasWrapper = previewPdfCanvasWrapper.value
  const key = `${currentPreviewRow.value?.id || ''}@@${blob?.size || 0}@@${blob?.type || ''}`
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
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = ''
  previewType.value = ''
  currentPreviewRow.value = null
  previewError.value = ''
  previewBlob.value = null
  previewPdfRenderedKey.value = ''
  if (previewPdfCanvasWrapper.value) {
    previewPdfCanvasWrapper.value.innerHTML = ''
  }
}

const download = async (row) => {
  try {
    const blob = await downloadTemplateFile(row.id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = row.file_name || `template.${row.file_type || 'bin'}`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '下载失败')
  }
}

onMounted(load)
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.table-scroll {
  width: 100%;
  overflow-x: auto;
}

.op-row {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  white-space: nowrap;
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

.preview-unsupported {
  padding: 16px;
}

.preview-loading {
  padding: 16px;
}
</style>
