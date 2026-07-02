<template>
  <div class="template-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ $t('incidentTemplateDetail.title') }}</span>
          <el-button @click="$router.back()">{{ $t('common.return') }}</el-button>
        </div>
      </template>

      <el-form :model="form" label-width="110px">
        <el-form-item :label="$t('incidentTemplateDetail.titleLabel')">
          <div class="localized-field">
            <el-input v-model="form.title_i18n.zh" :placeholder="$t('incidentTemplateDetail.titleZhPlaceholder')" />
            <el-input v-model="form.title_i18n.en" :placeholder="$t('incidentTemplateDetail.titleEnPlaceholder')" />
          </div>
        </el-form-item>
        <el-form-item :label="$t('incidentTemplateDetail.description')">
          <div class="localized-field">
            <el-input
              v-model="form.description_i18n.zh"
              type="textarea"
              :placeholder="$t('incidentTemplateDetail.descriptionZhPlaceholder')"
            />
            <el-input
              v-model="form.description_i18n.en"
              type="textarea"
              :placeholder="$t('incidentTemplateDetail.descriptionEnPlaceholder')"
            />
          </div>
        </el-form-item>
        <el-form-item :label="$t('incidentTemplateDetail.status')">
          <el-switch v-model="form.is_active" />
        </el-form-item>
        <el-form-item :label="$t('incidentTemplateDetail.templateMode')">
          <el-radio-group v-model="form.mode">
            <el-radio-button value="builder">{{ $t('incidentTemplateDetail.modeBuilder') }}</el-radio-button>
            <el-radio-button value="questions">{{ $t('incidentTemplateDetail.modeQuestions') }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template v-if="form.mode === 'questions'">
        <el-divider>{{ $t('incidentTemplateDetail.fieldList') }}</el-divider>

        <div v-for="(question, index) in form.questions" :key="question.id || index" class="question-item">
          <el-card>
            <div class="question-header">
              <span>{{ $t('incidentTemplateDetail.field') }} {{ index + 1 }}</span>
              <el-button type="danger" size="small" @click="handleDeleteQuestion(index)">{{ $t('common.delete') }}</el-button>
            </div>
            <el-form :model="question" label-width="110px">
              <el-form-item :label="$t('incidentTemplateDetail.fieldLabel')">
                <div class="localized-field">
                  <el-input v-model="question.title_i18n.zh" :placeholder="$t('incidentTemplateDetail.fieldZhPlaceholder')" />
                  <el-input v-model="question.title_i18n.en" :placeholder="$t('incidentTemplateDetail.fieldEnPlaceholder')" />
                </div>
              </el-form-item>
              <el-form-item :label="$t('incidentTemplateDetail.type')">
                <el-select v-model="question.type">
                  <el-option :label="$t('incidentTemplateDetail.singleChoice')" value="single_choice" />
                  <el-option :label="$t('incidentTemplateDetail.multipleChoice')" value="multiple_choice" />
                  <el-option :label="$t('incidentTemplateDetail.text')" value="text" />
                  <el-option :label="$t('incidentTemplateDetail.number')" value="number" />
                  <el-option :label="$t('incidentTemplateDetail.date')" value="date" />
                </el-select>
              </el-form-item>
              <el-form-item :label="$t('incidentTemplateDetail.required')">
                <el-switch v-model="question.required" />
              </el-form-item>
              <el-form-item v-if="isChoiceQuestion(question.type)" :label="$t('incidentTemplateDetail.options')">
                <div class="option-list">
                  <div v-for="(option, optionIndex) in question.options" :key="option.id || optionIndex" class="option-item">
                    <div class="option-fields">
                      <el-input v-model="option.text_i18n.zh" :placeholder="$t('incidentTemplateDetail.optionZhPlaceholder')" />
                      <el-input v-model="option.text_i18n.en" :placeholder="$t('incidentTemplateDetail.optionEnPlaceholder')" />
                    </div>
                    <el-button type="danger" size="small" plain @click="removeOption(question, optionIndex)">
                      {{ $t('common.delete') }}
                    </el-button>
                  </div>
                  <el-button type="primary" plain size="small" @click="addOption(question)">
                    {{ $t('incidentTemplateDetail.addOption') }}
                  </el-button>
                </div>
              </el-form-item>
            </el-form>
          </el-card>
        </div>

        <el-button type="primary" @click="handleAddQuestion" style="margin-top: 20px">
          {{ $t('incidentTemplateDetail.addField') }}
        </el-button>
      </template>

      <template v-else>
        <el-divider>{{ $t('incidentTemplateDetail.layoutBuilder') }}</el-divider>

        <div class="builder-toolbar">
          <el-button type="primary" plain @click="addBlock('text')">{{ $t('incidentTemplateDetail.addTextBlock') }}</el-button>
          <el-button type="primary" plain @click="addBlock('divider')">{{ $t('incidentTemplateDetail.addDividerBlock') }}</el-button>
          <el-button type="primary" plain @click="addBlock('table')">{{ $t('incidentTemplateDetail.addTableBlock') }}</el-button>
        </div>

        <div v-for="(block, bIndex) in form.builder.blocks" :key="block.id" class="builder-block">
          <el-card>
            <div class="builder-block-header">
              <span>{{ $t('incidentTemplateDetail.block') }} {{ bIndex + 1 }} · {{ blockTypeLabel(block.type) }}</span>
              <el-button type="danger" size="small" @click="removeBlock(bIndex)">{{ $t('common.delete') }}</el-button>
            </div>

            <template v-if="block.type === 'text'">
              <el-form :model="block" label-width="110px">
                <el-form-item :label="$t('incidentTemplateDetail.textContent')">
                  <div class="localized-field">
                    <el-input v-model="block.text_i18n.zh" :placeholder="$t('incidentTemplateDetail.textZhPlaceholder')" />
                    <el-input v-model="block.text_i18n.en" :placeholder="$t('incidentTemplateDetail.textEnPlaceholder')" />
                  </div>
                </el-form-item>
                <el-form-item :label="$t('incidentTemplateDetail.textStyle')">
                  <div class="builder-style-row">
                    <el-input-number v-model="block.style.fontSize" :min="10" :max="40" />
                    <el-switch v-model="block.style.bold" />
                    <el-select v-model="block.style.align" style="width: 140px">
                      <el-option :label="$t('incidentTemplateDetail.alignLeft')" value="left" />
                      <el-option :label="$t('incidentTemplateDetail.alignCenter')" value="center" />
                      <el-option :label="$t('incidentTemplateDetail.alignRight')" value="right" />
                    </el-select>
                    <el-input v-model="block.style.color" style="width: 140px" :placeholder="$t('incidentTemplateDetail.colorPlaceholder')" />
                  </div>
                </el-form-item>
              </el-form>
            </template>

            <template v-else-if="block.type === 'divider'">
              <el-divider />
            </template>

            <template v-else-if="block.type === 'table'">
              <el-form :model="block" label-width="110px">
                <el-form-item :label="$t('incidentTemplateDetail.tableSize')">
                  <div class="builder-style-row">
                    <el-input-number v-model="block.rows" :min="1" :max="30" />
                    <el-input-number v-model="block.cols" :min="1" :max="12" />
                    <el-button type="primary" plain @click="applyTableSize(block)">{{ $t('incidentTemplateDetail.applySize') }}</el-button>
                    <el-button type="danger" plain @click="resetTableCells(block)">{{ $t('incidentTemplateDetail.resetCells') }}</el-button>
                  </div>
                </el-form-item>
                <el-form-item :label="$t('incidentTemplateDetail.colWidths')">
                  <div class="builder-colwidths">
                    <div v-for="c in block.cols" :key="c" class="builder-colwidth">
                      <div class="builder-colwidth-label">{{ $t('incidentTemplateDetail.col') }} {{ c }}</div>
                      <el-input-number v-model="block.colWidths[c - 1]" :min="40" :max="480" />
                    </div>
                  </div>
                </el-form-item>
              </el-form>

              <div class="builder-table-wrap">
                <table class="builder-table" :style="tableStyle(block)">
                  <colgroup>
                    <col v-for="c in block.cols" :key="c" :style="columnStyle(block, c - 1)" />
                  </colgroup>
                  <tbody>
                    <tr v-for="r in block.rows" :key="r">
                      <template v-for="c in block.cols" :key="`${r}-${c}`">
                        <td
                          v-if="!isCellCovered(block, r - 1, c - 1)"
                          class="builder-td"
                          :rowspan="getCellSpan(block, r - 1, c - 1).rowSpan"
                          :colspan="getCellSpan(block, r - 1, c - 1).colSpan"
                          @click="openCellEditor(block, r - 1, c - 1)"
                        >
                          <div class="builder-cell-preview">
                            <div class="builder-cell-type">{{ cellPreviewType(block, r - 1, c - 1) }}</div>
                            <div class="builder-cell-text">{{ cellPreviewText(block, r - 1, c - 1) }}</div>
                            <div class="builder-cell-key">{{ cellPreviewKey(block, r - 1, c - 1) }}</div>
                          </div>
                        </td>
                      </template>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
          </el-card>
        </div>
      </template>

      <div style="margin-top: 20px">
        <el-button @click="$router.back()">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave">{{ $t('common.save') }}</el-button>
      </div>
    </el-card>

    <el-dialog v-model="cellEditor.visible" :title="$t('incidentTemplateDetail.cellConfig')" width="680px">
      <el-form :model="cellEditor" label-width="130px">
        <el-form-item :label="$t('incidentTemplateDetail.cellType')">
          <el-select v-model="cellEditor.type" style="width: 260px">
            <el-option :label="$t('incidentTemplateDetail.cellEmpty')" value="empty" />
            <el-option :label="$t('incidentTemplateDetail.cellLabel')" value="label" />
            <el-option :label="$t('incidentTemplateDetail.cellInput')" value="input" />
            <el-option :label="$t('incidentTemplateDetail.cellTextarea')" value="textarea" />
            <el-option :label="$t('incidentTemplateDetail.cellSelect')" value="select" />
            <el-option :label="$t('incidentTemplateDetail.cellDatetime')" value="datetime" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="cellEditor.type === 'label'" :label="$t('incidentTemplateDetail.textContent')">
          <div class="localized-field">
            <el-input v-model="cellEditor.text_i18n.zh" :placeholder="$t('incidentTemplateDetail.textZhPlaceholder')" />
            <el-input v-model="cellEditor.text_i18n.en" :placeholder="$t('incidentTemplateDetail.textEnPlaceholder')" />
          </div>
        </el-form-item>

        <template v-if="cellNeedsBinding(cellEditor.type)">
          <el-form-item :label="$t('incidentTemplateDetail.bindingTarget')">
            <el-select v-model="cellEditor.bindingTarget" style="width: 260px">
              <el-option :label="$t('incidentTemplateDetail.bindingAccidentType')" value="incident_type" />
              <el-option :label="$t('incidentTemplateDetail.bindingDescription')" value="description" />
              <el-option :label="$t('incidentTemplateDetail.bindingOccurredAt')" value="occurred_at" />
              <el-option :label="$t('incidentTemplateDetail.bindingCustom')" value="custom" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="cellEditor.bindingTarget === 'custom'" :label="$t('incidentTemplateDetail.bindingKey')">
            <el-input v-model="cellEditor.bindingKey" :placeholder="$t('incidentTemplateDetail.bindingKeyPlaceholder')" />
            <div class="builder-help">{{ $t('incidentTemplateDetail.bindingHelp') }}</div>
          </el-form-item>
          <el-form-item :label="$t('incidentTemplateDetail.required')">
            <el-switch v-model="cellEditor.required" />
          </el-form-item>
        </template>

        <template v-if="cellEditor.type === 'select'">
          <el-form-item :label="$t('incidentTemplateDetail.selectOptions')">
            <div class="builder-option-list">
              <div v-for="(opt, idx) in cellEditor.options" :key="opt.value || idx" class="builder-option-item">
                <el-input v-model="opt.value" style="width: 120px" :placeholder="$t('incidentTemplateDetail.optionValue')" />
                <el-input v-model="opt.text_i18n.zh" style="width: 180px" :placeholder="$t('incidentTemplateDetail.optionZhPlaceholder')" />
                <el-input v-model="opt.text_i18n.en" style="width: 180px" :placeholder="$t('incidentTemplateDetail.optionEnPlaceholder')" />
                <el-button type="danger" plain @click="cellEditor.options.splice(idx, 1)">{{ $t('common.delete') }}</el-button>
              </div>
              <el-button type="primary" plain @click="addSelectOption">{{ $t('incidentTemplateDetail.addOption') }}</el-button>
            </div>
          </el-form-item>
        </template>

        <el-form-item :label="$t('incidentTemplateDetail.mergeCells')">
          <div class="builder-style-row">
            <div class="builder-merge-item">
              <div class="builder-merge-label">{{ $t('incidentTemplateDetail.mergeCols') }}</div>
              <el-input-number v-model="cellEditor.colSpan" :min="1" :max="50" />
            </div>
            <div class="builder-merge-item">
              <div class="builder-merge-label">{{ $t('incidentTemplateDetail.mergeRows') }}</div>
              <el-input-number v-model="cellEditor.rowSpan" :min="1" :max="50" />
            </div>
          </div>
          <div class="builder-help">{{ $t('incidentTemplateDetail.mergeHelp') }}</div>
        </el-form-item>

        <el-form-item :label="$t('incidentTemplateDetail.cellStyle')">
          <div class="builder-style-row">
            <el-input-number v-model="cellEditor.style.fontSize" :min="10" :max="24" />
            <el-switch v-model="cellEditor.style.bold" />
            <el-select v-model="cellEditor.style.align" style="width: 140px">
              <el-option :label="$t('incidentTemplateDetail.alignLeft')" value="left" />
              <el-option :label="$t('incidentTemplateDetail.alignCenter')" value="center" />
              <el-option :label="$t('incidentTemplateDetail.alignRight')" value="right" />
            </el-select>
            <el-input v-model="cellEditor.style.color" style="width: 140px" :placeholder="$t('incidentTemplateDetail.colorPlaceholder')" />
            <el-input v-model="cellEditor.style.bgColor" style="width: 140px" :placeholder="$t('incidentTemplateDetail.bgColorPlaceholder')" />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="cellEditor.visible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="applyCellEditor">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'IncidentTemplateDetail' })
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getIncidentTemplate, updateIncidentTemplate, createIncidentTemplate } from '@/api/incidentTemplates'

const route = useRoute()
const router = useRouter()
const templateId = route.params.id
const loading = ref(false)

const form = reactive({
  title_i18n: { zh: '', en: '' },
  description_i18n: { zh: '', en: '' },
  is_active: true,
  mode: templateId === 'new' ? 'builder' : 'questions',
  questions: [],
  builder: {
    version: 1,
    blocks: []
  }
})

const normalizeString = (value) => (value == null ? '' : String(value)).trim()
const normalizeI18nText = (value, fallback = '') => {
  const next = { zh: '', en: '' }
  if (value && typeof value === 'object') {
    next.zh = normalizeString(value.zh || value['zh-CN'] || value.cn)
    next.en = normalizeString(value.en || value['en-US'])
  }
  if (!next.zh && !next.en) {
    const base = normalizeString(fallback)
    if (base) next.zh = base
  }
  return next
}

const normalizeOption = (option, idx) => {
  const textI18n = normalizeI18nText(option?.text_i18n, option?.text || '')
  return {
    id: option?.id ?? `opt${idx + 1}`,
    text_i18n: textI18n
  }
}

const normalizeQuestion = (q, idx) => {
  const titleI18n = normalizeI18nText(q?.title_i18n, q?.title || '')
  return {
    id: q?.id ?? `q${idx + 1}`,
    title_i18n: titleI18n,
    type: q?.type || 'single_choice',
    required: !!q?.required,
    options: Array.isArray(q?.options) ? q.options.map((o, i) => normalizeOption(o, i)) : []
  }
}

const createDefaultTextStyle = () => ({
  fontSize: 14,
  bold: false,
  align: 'left',
  color: '',
  bgColor: ''
})

const normalizeBuilderBlock = (block, idx) => {
  const type = block?.type || 'text'
  const id = block?.id ?? `b${idx + 1}`
  if (type === 'divider') {
    return { id, type: 'divider' }
  }
  if (type === 'table') {
    const rows = Number(block?.rows || 6)
    const cols = Number(block?.cols || 4)
    const colWidths = Array.isArray(block?.colWidths) ? block.colWidths.map((n) => Number(n) || 120) : Array(cols).fill(120)
    const cells = block?.cells && typeof block.cells === 'object' ? block.cells : {}
    return { id, type: 'table', rows, cols, colWidths: ensureArraySize(colWidths, cols, 120), cells }
  }
  const textI18n = normalizeI18nText(block?.text_i18n, block?.text || '')
  return { id, type: 'text', text_i18n: textI18n, style: { ...createDefaultTextStyle(), ...(block?.style || {}) } }
}

const normalizeBuilder = (schema) => {
  const blocks = schema?.blocks
  const list = Array.isArray(blocks) ? blocks : []
  return {
    version: Number(schema?.version || 1),
    blocks: list.map((b, idx) => normalizeBuilderBlock(b, idx))
  }
}

function ensureArraySize(arr, size, fillValue) {
  const next = Array.isArray(arr) ? [...arr] : []
  while (next.length < size) next.push(fillValue)
  if (next.length > size) next.length = size
  return next
}

const load = async () => {
  if (templateId === 'new') return
  loading.value = true
  try {
    const data = await getIncidentTemplate(templateId)
    form.title_i18n = normalizeI18nText(data?.title_i18n, data?.title)
    form.description_i18n = normalizeI18nText(data?.description_i18n, data?.description)
    form.is_active = data?.is_active !== false
    const schema = data?.schema_json
    if (schema?.kind === 'builder_v1') {
      form.mode = 'builder'
      form.builder = normalizeBuilder(schema)
      form.questions = []
    } else {
      form.mode = 'questions'
      const questions = schema?.questions || []
      form.questions = Array.isArray(questions) ? questions.map((q, idx) => normalizeQuestion(q, idx)) : []
      form.builder = { version: 1, blocks: [] }
    }
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleAddQuestion = () => {
  const nextIndex = form.questions.length + 1
  form.questions.push({
    id: `q${nextIndex}`,
    title_i18n: { zh: '', en: '' },
    type: 'single_choice',
    required: false,
    options: []
  })
}

const handleDeleteQuestion = (index) => {
  form.questions.splice(index, 1)
}

const isChoiceQuestion = (type) => type === 'single_choice' || type === 'multiple_choice'

const addOption = (question) => {
  if (!Array.isArray(question.options)) question.options = []
  const nextIndex = question.options.length + 1
  question.options.push({ id: `opt${nextIndex}`, text_i18n: { zh: '', en: '' } })
}

const removeOption = (question, optionIndex) => {
  if (!Array.isArray(question.options)) return
  question.options.splice(optionIndex, 1)
}

const newId = (prefix) => `${prefix}${Math.random().toString(36).slice(2, 8)}`

const blockTypeLabel = (type) => {
  if (type === 'text') return 'Text'
  if (type === 'divider') return 'Divider'
  if (type === 'table') return 'Table'
  return type || 'Unknown'
}

const addBlock = (type) => {
  if (!Array.isArray(form.builder.blocks)) form.builder.blocks = []
  if (type === 'divider') {
    form.builder.blocks.push({ id: newId('b'), type: 'divider' })
    return
  }
  if (type === 'table') {
    const rows = 6
    const cols = 4
    form.builder.blocks.push({
      id: newId('b'),
      type: 'table',
      rows,
      cols,
      colWidths: Array(cols).fill(120),
      cells: {}
    })
    return
  }
  form.builder.blocks.push({
    id: newId('b'),
    type: 'text',
    text_i18n: { zh: '', en: '' },
    style: createDefaultTextStyle()
  })
}

const removeBlock = (index) => {
  form.builder.blocks.splice(index, 1)
}

const applyTableSize = (block) => {
  const rows = Math.max(1, Number(block.rows) || 1)
  const cols = Math.max(1, Number(block.cols) || 1)
  block.rows = rows
  block.cols = cols
  block.colWidths = ensureArraySize(block.colWidths, cols, 120)

  const nextCells = {}
  const cells = block.cells && typeof block.cells === 'object' ? block.cells : {}
  Object.keys(cells).forEach((k) => {
    const parts = k.split(',')
    const r = Number(parts[0])
    const c = Number(parts[1])
    if (Number.isFinite(r) && Number.isFinite(c) && r >= 0 && c >= 0 && r < rows && c < cols) {
      nextCells[k] = cells[k]
    }
  })
  block.cells = nextCells
}

const resetTableCells = (block) => {
  block.cells = {}
}

const cellKey = (row, col) => `${row},${col}`
const getCell = (block, row, col) => {
  const cells = block?.cells
  if (!cells || typeof cells !== 'object') return null
  return cells[cellKey(row, col)] || null
}

const parseCellSpan = (cell) => {
  const span = cell?.span && typeof cell.span === 'object' ? cell.span : null
  const rowSpan = Math.max(1, Number(span?.rowSpan || 1) || 1)
  const colSpan = Math.max(1, Number(span?.colSpan || 1) || 1)
  return { rowSpan, colSpan }
}

const getCellSpan = (block, row, col) => {
  const cell = getCell(block, row, col)
  if (!cell) return { rowSpan: 1, colSpan: 1 }
  return parseCellSpan(cell)
}

const isCellCovered = (block, row, col) => {
  const cells = block?.cells && typeof block.cells === 'object' ? block.cells : {}
  const keys = Object.keys(cells)
  for (const k of keys) {
    const parts = k.split(',')
    const r0 = Number(parts[0])
    const c0 = Number(parts[1])
    if (!Number.isFinite(r0) || !Number.isFinite(c0)) continue
    const cell = cells[k]
    const span = parseCellSpan(cell)
    if (span.rowSpan <= 1 && span.colSpan <= 1) continue
    if (row === r0 && col === c0) continue
    if (row >= r0 && row < r0 + span.rowSpan && col >= c0 && col < c0 + span.colSpan) return true
  }
  return false
}

const cellPreviewType = (block, row, col) => {
  const cell = getCell(block, row, col)
  if (!cell) return ''
  return cell.type || ''
}

const cellPreviewText = (block, row, col) => {
  const cell = getCell(block, row, col)
  if (!cell) return ''
  if (cell.type === 'label') return normalizeString(cell?.text_i18n?.zh || cell?.text_i18n?.en)
  return ''
}

const cellPreviewKey = (block, row, col) => {
  const cell = getCell(block, row, col)
  if (!cell) return ''
  return normalizeString(cell?.binding?.key)
}

const columnStyle = (block, colIndex) => {
  const w = Number(block?.colWidths?.[colIndex] || 0)
  return w > 0 ? { width: `${w}px`, minWidth: `${w}px` } : {}
}

const tableStyle = (block) => {
  const widths = Array.isArray(block?.colWidths) ? block.colWidths : []
  const total = widths.reduce((sum, item) => sum + (Number(item) || 0), 0)
  return total > 0 ? { width: `${total}px` } : {}
}

const cellEditor = reactive({
  visible: false,
  blockId: '',
  row: 0,
  col: 0,
  type: 'empty',
  text_i18n: { zh: '', en: '' },
  bindingTarget: 'custom',
  bindingKey: '',
  required: false,
  rowSpan: 1,
  colSpan: 1,
  options: [],
  style: createDefaultTextStyle()
})

const cellNeedsBinding = (type) => type === 'input' || type === 'textarea' || type === 'select' || type === 'datetime'

const openCellEditor = (block, row, col) => {
  const existing = getCell(block, row, col)
  cellEditor.blockId = block.id
  cellEditor.row = row
  cellEditor.col = col
  cellEditor.type = existing?.type || 'empty'
  cellEditor.text_i18n = normalizeI18nText(existing?.text_i18n, existing?.text || '')
  const existingKey = normalizeString(existing?.binding?.key || '')
  cellEditor.bindingTarget = existingKey === 'incident_type' || existingKey === 'description' || existingKey === 'occurred_at' ? existingKey : 'custom'
  cellEditor.bindingKey = cellEditor.bindingTarget === 'custom' ? existingKey : ''
  cellEditor.required = !!existing?.required
  const span = parseCellSpan(existing)
  cellEditor.rowSpan = span.rowSpan
  cellEditor.colSpan = span.colSpan
  cellEditor.options = Array.isArray(existing?.options)
    ? existing.options.map((o) => ({
        value: normalizeString(o?.value || ''),
        text_i18n: normalizeI18nText(o?.text_i18n, o?.text || '')
      }))
    : []
  cellEditor.style = { ...createDefaultTextStyle(), ...(existing?.style || {}) }
  cellEditor.visible = true
}

const addSelectOption = () => {
  if (!Array.isArray(cellEditor.options)) cellEditor.options = []
  cellEditor.options.push({ value: '', text_i18n: { zh: '', en: '' } })
}

const rectIntersects = (a, b) => !(a.r2 <= b.r1 || a.r1 >= b.r2 || a.c2 <= b.c1 || a.c1 >= b.c2)

const applyCellEditor = () => {
  const block = form.builder.blocks.find((b) => b.id === cellEditor.blockId)
  if (!block || block.type !== 'table') {
    cellEditor.visible = false
    return
  }

  const type = cellEditor.type
  const k = cellKey(cellEditor.row, cellEditor.col)
  if (type === 'empty') {
    if (block.cells && typeof block.cells === 'object') delete block.cells[k]
    cellEditor.visible = false
    return
  }

  const maxRowSpan = Math.max(1, Number(block.rows || 1) - Number(cellEditor.row || 0))
  const maxColSpan = Math.max(1, Number(block.cols || 1) - Number(cellEditor.col || 0))
  const rowSpan = Math.min(maxRowSpan, Math.max(1, Number(cellEditor.rowSpan || 1) || 1))
  const colSpan = Math.min(maxColSpan, Math.max(1, Number(cellEditor.colSpan || 1) || 1))

  const newRect = { r1: cellEditor.row, c1: cellEditor.col, r2: cellEditor.row + rowSpan, c2: cellEditor.col + colSpan }
  const cells = block.cells && typeof block.cells === 'object' ? block.cells : {}
  for (const key of Object.keys(cells)) {
    if (key === k) continue
    const parts = key.split(',')
    const r0 = Number(parts[0])
    const c0 = Number(parts[1])
    if (!Number.isFinite(r0) || !Number.isFinite(c0)) continue
    const cell = cells[key]
    const span = parseCellSpan(cell)
    if (span.rowSpan <= 1 && span.colSpan <= 1) continue
    const rect = { r1: r0, c1: c0, r2: r0 + span.rowSpan, c2: c0 + span.colSpan }
    if (rectIntersects(newRect, rect)) {
      ElMessage.error('合并区域与已有合并单元格冲突，请先调整已有合并')
      return
    }
  }

  if (type === 'label') {
    block.cells[k] = {
      type: 'label',
      text_i18n: { ...cellEditor.text_i18n },
      style: { ...cellEditor.style },
      span: rowSpan > 1 || colSpan > 1 ? { rowSpan, colSpan } : undefined
    }
    if (rowSpan > 1 || colSpan > 1) {
      for (let rr = cellEditor.row; rr < cellEditor.row + rowSpan; rr++) {
        for (let cc = cellEditor.col; cc < cellEditor.col + colSpan; cc++) {
          if (rr === cellEditor.row && cc === cellEditor.col) continue
          delete block.cells[cellKey(rr, cc)]
        }
      }
    }
    cellEditor.visible = false
    return
  }

  const bindingKey = cellEditor.bindingTarget === 'custom'
    ? normalizeString(cellEditor.bindingKey)
    : normalizeString(cellEditor.bindingTarget)
  if (!bindingKey) {
    ElMessage.error('binding key 不能为空')
    return
  }

  const next = {
    type,
    binding: { key: bindingKey },
    required: !!cellEditor.required,
    style: { ...cellEditor.style },
    span: rowSpan > 1 || colSpan > 1 ? { rowSpan, colSpan } : undefined
  }
  if (type === 'select') {
    next.options = (Array.isArray(cellEditor.options) ? cellEditor.options : [])
      .map((o) => ({
        value: normalizeString(o.value),
        text_i18n: normalizeI18nText(o.text_i18n, o.value)
      }))
      .filter((o) => !!o.value)
  }
  block.cells[k] = next
  if (rowSpan > 1 || colSpan > 1) {
    for (let rr = cellEditor.row; rr < cellEditor.row + rowSpan; rr++) {
      for (let cc = cellEditor.col; cc < cellEditor.col + colSpan; cc++) {
        if (rr === cellEditor.row && cc === cellEditor.col) continue
        delete block.cells[cellKey(rr, cc)]
      }
    }
  }
  cellEditor.visible = false
}

const collectBuilderBindingKeys = () => {
  const keys = []
  const blocks = Array.isArray(form.builder.blocks) ? form.builder.blocks : []
  blocks.forEach((b) => {
    if (b.type !== 'table') return
    const cells = b.cells && typeof b.cells === 'object' ? b.cells : {}
    Object.keys(cells).forEach((k) => {
      const cell = cells[k]
      const key = normalizeString(cell?.binding?.key)
      if (key) keys.push(key)
    })
  })
  return keys
}

const handleSave = async () => {
  const payload = {
    title: normalizeString(form.title_i18n.zh || form.title_i18n.en),
    title_i18n: form.title_i18n,
    description: normalizeString(form.description_i18n.zh || form.description_i18n.en),
    description_i18n: form.description_i18n,
    is_active: form.is_active,
    schema_json: null,
    style_json: null
  }
  if (form.mode === 'builder') {
    const keys = collectBuilderBindingKeys()
    const keyRegex = /^[a-zA-Z][a-zA-Z0-9_]*$/
    for (const k of keys) {
      if (!keyRegex.test(k)) {
        ElMessage.error(`binding key 不合法: ${k}`)
        return
      }
    }
    const seen = new Set()
    const dup = keys.find((k) => (seen.has(k) ? true : (seen.add(k), false)))
    if (dup) {
      ElMessage.error(`binding key 重复: ${dup}`)
      return
    }
    payload.schema_json = { kind: 'builder_v1', version: 1, blocks: form.builder.blocks }
    payload.style_json = { preset: 'builder_v1' }
  } else {
    payload.schema_json = { questions: form.questions }
    payload.style_json = { preset: 'default' }
  }
  try {
    if (templateId === 'new') {
      await createIncidentTemplate(payload)
      ElMessage.success('创建成功')
    } else {
      await updateIncidentTemplate(templateId, payload)
      ElMessage.success('保存成功')
    }
    router.push('/incident-templates/templates')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || e?.message || '保存失败')
  }
}

load()
</script>

<style scoped>
.template-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.localized-field,
.option-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
}

.question-item {
  margin-bottom: 16px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.option-list {
  width: 100%;
}

.option-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin-bottom: 10px;
}

.builder-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.builder-block {
  margin-bottom: 16px;
}

.builder-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.builder-style-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.builder-table-wrap {
  overflow-x: auto;
}

.builder-table {
  border-collapse: collapse;
  width: max-content;
  min-width: 100%;
}

.builder-td {
  border: 1px solid #e5e7eb;
  height: 46px;
  cursor: pointer;
  background: #fff;
  vertical-align: middle;
}

.builder-td:hover {
  background: #f5f7fa;
}

.builder-cell-preview {
  padding: 6px 8px;
  display: grid;
  gap: 2px;
}

.builder-cell-type {
  font-size: 12px;
  color: #6b7280;
}

.builder-cell-text {
  font-size: 13px;
  color: #111827;
}

.builder-cell-key {
  font-size: 12px;
  color: #2563eb;
}

.builder-colwidths {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
  width: 100%;
}

.builder-colwidth {
  display: flex;
  gap: 10px;
  align-items: center;
}

.builder-colwidth-label {
  width: 70px;
  color: #6b7280;
  font-size: 12px;
}

.builder-merge-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.builder-merge-label {
  width: 92px;
  color: #6b7280;
  font-size: 12px;
}

.builder-option-list {
  width: 100%;
  display: grid;
  gap: 10px;
}

.builder-option-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.builder-help {
  margin-top: 6px;
  font-size: 12px;
  color: #6b7280;
}
</style>
