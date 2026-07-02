<template>
  <div class="customer-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            {{ $t('customer.addCustomer') }}
            </el-button>
          </div>
        </div>
      </template>
      
      <el-tabs v-model="activeTypeTab" class="type-tabs">
        <el-tab-pane :label="$t('customer.typeAll')" name="all" />
        <el-tab-pane :label="$t('customer.elderly')" name="养老" />
        <el-tab-pane :label="$t('customer.disability')" name="助残" />
        <el-tab-pane :label="$t('customer.ndis')" name="NDIS" />
      </el-tabs>

      <div class="table-toolbar">
        <el-input
          v-model="searchName"
          :placeholder="t('customer.searchPlaceholder')"
          clearable
          class="search-input"
        />
      </div>

      <el-table
        :data="pagedCustomers"
        v-loading="loading"
        stripe
        table-layout="auto"
        :default-sort="{ prop: 'last_service_time', order: 'descending' }"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="customer_code" :label="$t('customer.customerCode')" width="130">
          <template #default="{ row }">
            <span class="clickable-with-dot">
              <span v-if="row.has_update" class="row-dot" />
              <el-link type="primary" class="clickable-text" :underline="true" @click="handleView(row)">{{ row.customer_code || '-' }}</el-link>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="name" :label="$t('customer.name')" width="130">
          <template #default="{ row }">
            <span class="clickable-with-dot">
              <span v-if="row.has_update" class="row-dot" />
              <el-link type="primary" class="clickable-text" :underline="true" @click="handleView(row)">{{ row.name || '-' }}</el-link>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="phone" :label="$t('customer.phone')" width="160" />
        <el-table-column prop="email" :label="$t('customer.email')" min-width="270" />
        <el-table-column prop="address" :label="$t('customer.address')" min-width="270" />
        <el-table-column prop="customer_status" :label="$t('customer.status')" width="130">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.customer_status)">{{ getCustomerStatusText(row.customer_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_type" :label="$t('customer.type')" width="130">
          <template #default="{ row }">
            <span>{{ getCustomerTypeText(row.customer_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="service_count" :label="$t('customer.serviceCount')" width="130" />
        <el-table-column :label="$t('customer.weeklyServiceHours')" width="150">
          <template #default="{ row }">
            <span>{{ row.weekly_service_hours != null ? Number(row.weekly_service_hours).toFixed(2) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('customer.weeklyServedHours')" width="170">
          <template #default="{ row }">
            <span>{{ row.weekly_served_hours != null ? Number(row.weekly_served_hours).toFixed(2) : '0.00' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_service_time" column-key="last_service_time" :label="$t('customer.lastServiceTime')" width="260" sortable="custom">
          <template #default="{ row }">
            <span>{{ row.last_service_time || $t('customer.none') }}</span>
          </template>
        </el-table-column>
        <el-table-column :label="$t('customer.operations')" width="180" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
          <template #default="{ row }">
            <template v-if="isNotBuiltStatus(row.customer_status)">
              <div class="action-buttons action-buttons--scroll">
                <div class="action-buttons-inner">
                  <el-button type="primary" size="small" @click="openUploadContract(row)">{{ $t('customer.uploadContract') }}</el-button>
                  <el-button size="small" :disabled="!row.hasAgreement" @click="sendContract(row)">{{ $t('customer.sendContract') }}</el-button>
                  <el-button type="success" size="small" :disabled="!row.hasAgreement" @click="startReviewRow(row)">{{ $t('customer.startReview') }}</el-button>
                  <el-button type="danger" size="small" @click="handleDelete(row)">{{ $t('customer.delete') }}</el-button>
                </div>
              </div>
            </template>
            <template v-else-if="isPendingStatus(row.customer_status)">
              <div class="action-buttons action-buttons--scroll">
                <div class="action-buttons-inner">
                  <el-button size="small" @click="viewSignedContract(row)">{{ $t('common.view') }}</el-button>
                  <el-button type="success" size="small" @click="approveRow(row)">{{ $t('customer.approve') }}</el-button>
                  <el-button type="warning" size="small" @click="rejectRow(row)">{{ $t('customer.reject') }}</el-button>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="action-buttons">
                <el-button type="primary" size="small" @click="handleEdit(row)">{{ $t('customer.edit') }}</el-button>
                <el-button type="danger" size="small" @click="handleDelete(row)">{{ $t('customer.delete') }}</el-button>
              </div>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-bar">
        <el-pagination
          v-model:current-page="customerPage"
          v-model:page-size="customerPageSize"
          :page-sizes="[10]"
          layout="total, prev, pager, next"
          :total="customerTotal"
        />
      </div>
    </el-card>
    
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="760px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="auto" class="customer-form">
        <el-form-item :label="$t('customer.name')" prop="name" class="form-item-medium">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="$t('customer.phone')" prop="phone" class="form-item-compact">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item :label="$t('customer.address')" prop="address">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item :label="$t('customer.email')" prop="email" class="form-item-medium">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item :label="$t('customer.type')" prop="customer_type" class="form-item-compact">
          <el-select v-model="form.customer_type" :placeholder="$t('customer.selectType')">
            <el-option :label="$t('customer.elderly')" value="养老" />
            <el-option :label="$t('customer.disability')" value="助残" />
            <el-option :label="$t('customer.ndis')" value="NDIS" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('customer.weeklyServiceHours')" prop="weekly_service_hours" class="form-item-compact">
          <el-input-number v-model="form.weekly_service_hours" :min="0" :precision="2" :step="0.5" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="$t('customer.weeklyServedHours')" class="form-item-compact">
          <el-input-number v-model="form.weekly_served_hours" :min="0" :precision="2" :step="0.5" controls-position="right" style="width: 100%" disabled />
        </el-form-item>
        <el-form-item :label="$t('customer.acceptedServiceLevel')" prop="accepted_service_level1_ids" class="form-item-medium">
          <el-select
            v-model="form.accepted_service_level1_ids"
            multiple
            filterable
            collapse-tags
            :placeholder="$t('customer.selectAcceptedServiceLevel')"
          >
            <el-option
              v-for="opt in serviceLevelOptions"
              :key="opt.id"
              :label="opt.name"
              :value="opt.id"
            />
          </el-select>
        </el-form-item>
        <template v-if="form.customer_type === 'NDIS'">
          <el-form-item :label="$t('customer.ndisNumber')" prop="ndis_number" class="form-item-medium">
            <el-input v-model="form.ndis_number" :placeholder="$t('customer.ndisNumberPlaceholder')" />
          </el-form-item>
          <el-form-item :label="$t('customer.ndisFundingType')" class="form-item-medium">
            <el-select v-model="form.ndis_funding_type" :placeholder="$t('customer.selectNdisFundingType')" clearable>
              <el-option :label="$t('customer.ndisManaged')" value="NDIS Managed" />
              <el-option :label="$t('customer.selfManaged')" value="Self-Managed" />
              <el-option :label="$t('customer.planManaged')" value="Plan Managed" />
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('customer.aboriginalTorresStrait')" class="form-item-medium">
            <el-checkbox v-model="form.aboriginal_torres_strait">{{ $t('customer.aboriginalTorresStraitLabel') }}</el-checkbox>
          </el-form-item>
          <el-form-item :label="$t('customer.ndisPlanFile')" class="form-item-medium">
            <el-upload
              :auto-upload="false"
              :file-list="ndisPlanFileList"
              :on-change="handleNdisPlanChange"
              :on-remove="handleNdisPlanRemove"
              :limit="1"
              accept=".pdf,.doc,.docx"
            >
              <el-button type="primary">{{ $t('customer.uploadNdisPlan') }}</el-button>
            </el-upload>
            <div v-if="form.id && viewNdisPlanName" class="ndis-plan-existing">
              {{ $t('customer.currentFile') }}: {{ viewNdisPlanName }}
            </div>
          </el-form-item>
        </template>
        <el-form-item :label="$t('customer.gender')" prop="gender" class="form-item-compact">
          <el-select v-model="form.gender" :placeholder="$t('customer.selectGender')">
            <el-option :label="$t('customer.male')" value="男" />
            <el-option :label="$t('customer.female')" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('customer.age')" prop="age" class="form-item-compact">
          <el-input-number v-model="form.age" :min="0" :max="120" />
        </el-form-item>
        <el-form-item :label="$t('customer.disabilityType')" prop="disability_type" class="form-item-medium">
          <el-input v-model="form.disability_type" />
        </el-form-item>
        <template v-if="!HIDE_PHONY_CUSTOMER_FIELDS">
          <el-divider content-position="left">{{ $t('customer.medicalCardSection') }}</el-divider>
          <el-form-item :label="$t('customer.hasMedicalCard')" class="form-item-medium">
            <el-radio-group v-model="form.has_medical_card">
              <el-radio :label="true">{{ $t('common.yes') }}</el-radio>
              <el-radio :label="false">{{ $t('common.no') }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="form.has_medical_card === true" :label="$t('customer.medicalCardNumber')" prop="medical_card_number" class="form-item-medium">
            <el-input v-model="form.medical_card_number" />
          </el-form-item>
          <el-divider content-position="left">{{ $t('customer.medicareSection') }}</el-divider>
          <el-form-item :label="$t('customer.medicareNumber')" class="form-item-medium">
            <el-input v-model="form.medicare_number" />
          </el-form-item>
          <el-form-item :label="$t('customer.medicareExpiry')" class="form-item-medium">
            <el-date-picker v-model="form.medicare_expiry" type="date" :placeholder="$t('customer.selectMedicareExpiry')" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
          <el-divider content-position="left">{{ $t('customer.privateHealthSection') }}</el-divider>
          <el-form-item :label="$t('customer.privateHealthFund')" class="form-item-medium">
            <el-input v-model="form.private_health_fund" />
          </el-form-item>
          <el-form-item :label="$t('customer.privatePolicyNumber')" class="form-item-medium">
            <el-input v-model="form.private_policy_number" />
          </el-form-item>
          <el-divider content-position="left">{{ $t('customer.invoiceReceiverSection') }}</el-divider>
          <el-form-item :label="$t('customer.invoiceReceiverName')" class="form-item-medium">
            <el-input v-model="form.invoice_receiver_name" />
          </el-form-item>
          <el-form-item :label="$t('customer.invoiceReceiverPhone')" class="form-item-medium">
            <el-input v-model="form.invoice_receiver_phone" />
          </el-form-item>
          <el-form-item :label="$t('customer.invoiceReceiverEmail')" class="form-item-medium">
            <el-input v-model="form.invoice_receiver_email" />
          </el-form-item>
          <el-form-item :label="$t('customer.invoiceReceiverAddress')" class="form-item-medium">
            <el-input v-model="form.invoice_receiver_address" type="textarea" />
          </el-form-item>
        </template>
        <el-divider content-position="left">{{ $t('customer.emergencyContactSection') }}</el-divider>
        <el-form-item :label="$t('customer.emergencyContact1Name')" prop="emergency_contact1_name" class="form-item-medium">
          <el-input v-model="form.emergency_contact1_name" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact1Phone')" prop="emergency_contact1_phone" class="form-item-medium">
          <el-input v-model="form.emergency_contact1_phone" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact1Email')" prop="emergency_contact1_email" class="form-item-medium">
          <el-input v-model="form.emergency_contact1_email" />
        </el-form-item>
        <el-divider content-position="left">{{ $t('customer.emergencyContact2Section') }}</el-divider>
        <el-form-item :label="$t('customer.emergencyContact2Name')" class="form-item-medium">
          <el-input v-model="form.emergency_contact2_name" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact2Phone')" class="form-item-medium">
          <el-input v-model="form.emergency_contact2_phone" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact2Email')" class="form-item-medium">
          <el-input v-model="form.emergency_contact2_email" />
        </el-form-item>
        <el-form-item :label="$t('customer.introduction')" prop="introduction">
          <el-input v-model="form.introduction" type="textarea" />
        </el-form-item>
        <el-form-item :label="$t('customer.notes')" prop="notes">
          <el-input v-model="form.notes" type="textarea" />
        </el-form-item>
        <el-form-item :label="$t('customer.attachments')">
          <el-upload
            :auto-upload="false"
            multiple
            :file-list="attachmentList"
            :on-change="handleAttachmentChange"
            :on-remove="handleAttachmentRemove"
          >
            <el-button type="primary">{{ $t('customer.selectFile') }}</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="uploadContractDialogVisible" :title="$t('customer.uploadContractDialogTitle')" width="640px">
      <el-alert :title="$t('customer.uploadContractModeHint')" type="info" :closable="false" style="margin-bottom: 10px;" />
      <el-tabs v-model="uploadContractMode" class="mode-tabs">
        <el-tab-pane :label="$t('customer.chooseFromTemplate')" name="template">
          <div class="template-select-row">
            <el-select
              v-model="selectedTemplateId"
              :placeholder="$t('customer.selectTemplatePlaceholder')"
              style="width: 100%"
              filterable
              clearable
              :loading="loadingTemplates"
            >
              <el-option v-for="t in templateOptions" :key="t.id" :label="t.template_name" :value="t.id" />
            </el-select>
          </div>
          <div class="template-actions">
            <el-button @click="loadTemplates">{{ $t('common.refresh') }}</el-button>
          </div>
        </el-tab-pane>
        <el-tab-pane :label="$t('customer.uploadLocalFile')" name="local">
          <el-upload
            :auto-upload="false"
            :file-list="uploadContractFileList"
            :on-change="handleContractFileChange"
            :limit="1"
            accept=".pdf,.doc,.docx"
          >
            <el-button type="primary">{{ $t('common.selectFile') }}</el-button>
          </el-upload>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="closeUploadContractDialog">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!canSubmitUploadContract" @click="submitUploadContract">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="sendContractDialogVisible" :title="$t('customer.sendContract')" width="360px">
      <el-form label-width="80px">
        <el-form-item :label="$t('common.language')">
          <el-select v-model="sendContractLang" style="width: 100%">
            <el-option :label="$t('common.chinese')" value="zh" />
            <el-option :label="$t('common.english')" value="en" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendContractDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="sendingContract" @click="submitSendContract">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="contractPreviewDialogVisible"
      :title="contractPreviewTitle"
      width="90%"
      top="5vh"
      @close="closeContractPreview"
    >
      <div class="preview-wrapper">
        <div v-if="contractPreviewType === 'pdfjs'" ref="contractPreviewPdfContainer" class="preview-pdfjs">
          <div ref="contractPreviewPdfCanvasWrapper" class="preview-pdfjs-canvases"></div>
        </div>
        <iframe v-else-if="contractPreviewUrl" :src="contractPreviewUrl" class="preview-iframe"></iframe>
        <div v-else class="preview-loading">{{ $t('common.loading') }}</div>
      </div>
      <template #footer>
        <el-button @click="contractPreviewDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
    
  </div>
</template>

<script setup>
defineOptions({
  name: 'Customers'
})
const HIDE_PHONY_CUSTOMER_FIELDS = true
import { ref, reactive, onMounted, computed, watch, inject, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getCustomers,
  createCustomer,
  updateCustomer,
  deleteCustomer,
  uploadCustomerAttachment,
  uploadNdisPlan,
  uploadCustomerContract,
  sendCustomerContract,
  viewCustomerContract,
  startArchiveReview,
  approveArchive,
  rejectArchive,
  deleteCustomerContract
} from '@/api/customers'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { getCustomerDocuments } from '@/api/customerDocuments'
import { getInvoiceServiceLevels } from '@/api/customers'
import { markUpdatesRead } from '@/api/updates'
import { getTemplateFiles } from '@/api/templateFiles'
import * as pdfjsDistLegacy from 'pdfjs-dist/legacy/build/pdf.js'
import pdfjsDistLegacyWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min.js?url'

const { t } = useI18n()
const router = useRouter()
const isMobile = inject('isMobile', ref(false))
const route = useRoute()
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

const pageTitle = computed(() => {
  const base = t('customer.title')
  const status = route.meta?.customerStatus
  return status ? `${base}/${getCustomerStatusText(status)}` : base
})

const customers = ref([])
const loading = ref(false)
const customerPage = ref(1)
const customerPageSize = ref(10)
const dialogVisible = ref(false)
const formRef = ref(null)
const searchName = ref('')
const attachmentList = ref([])
const ndisPlanFileList = ref([])
const viewNdisPlanName = ref('')
const activeStatusTab = ref('已建档')
const activeTypeTab = ref('all')
const uploadContractDialogVisible = ref(false)
const uploadContractFileList = ref([])
const uploadContractMode = ref('template')
const templateOptions = ref([])
const selectedTemplateId = ref('')
const loadingTemplates = ref(false)
const currentCustomerId = ref('')
const serviceLevelOptions = ref([])
const sendContractDialogVisible = ref(false)
const sendContractLang = ref('zh')
const sendingContract = ref(false)
const pendingSendContractRow = ref(null)
const pendingListMarkedRead = ref(false)

const contractPreviewDialogVisible = ref(false)
const contractPreviewType = ref('')
const contractPreviewUrl = ref('')
const contractPreviewRow = ref(null)
const contractPreviewBlob = ref(null)
const contractPreviewPdfContainer = ref(null)
const contractPreviewPdfCanvasWrapper = ref(null)
const contractPreviewPdfRenderedKey = ref('')

const contractPreviewTitle = computed(() => {
  const code = contractPreviewRow.value?.customer_code || ''
  const name = contractPreviewRow.value?.name || ''
  const base = t('common.preview')
  const text = [code, name].filter(Boolean).join(' ')
  return text ? `${base}: ${text}` : base
})

const normalizeCustomerStatus = (status) => (status || '').toString().trim()

const isNotBuiltStatus = (status) => normalizeCustomerStatus(status) === '未建档'
const isPendingStatus = (status) => normalizeCustomerStatus(status) === '待建档'

const getCustomerStatusText = (status) => {
  const s = normalizeCustomerStatus(status)
  if (!s) return '-'
  const map = {
    未建档: t('customer.statusNotBuilt'),
    待建档: t('customer.statusPending'),
    已建档: t('customer.statusBuilt'),
  }
  return map[s] || s
}

const getCustomerTypeText = (type) => {
  const v = (type || '').toString().trim()
  if (!v) return '-'
  const map = {
    NDIS: t('customer.ndis'),
    养老: t('customer.elderly'),
    助残: t('customer.disability'),
  }
  return map[v] || v
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

const loadServiceLevels = async () => {
  try {
    const res = await getInvoiceServiceLevels()
    const rows = getArrayFromResponse(res)
    serviceLevelOptions.value = rows
      .map((item) => ({
        id:
          item?.id ??
          item?.service_level_id ??
          item?.serviceLevelId ??
          item?.value ??
          item?.code ??
          item?.key,
        name:
          item?.name ??
          item?.service_level_name ??
          item?.serviceLevelName ??
          item?.label ??
          item?.title ??
          item?.text
      }))
      .filter((i) => i.id !== undefined && i.id !== null && i.name)
  } catch (e) {
    serviceLevelOptions.value = []
    const msg = e?.response?.data?.detail || e?.message || ''
    ElMessage.error(t('customer.loadServiceLevelsFailed') + (msg ? `：${msg}` : ''))
  }
}

const dialogTitle = computed(() => {
  return form.id ? t('customer.editCustomer') : t('customer.addCustomer')
})
const sortState = reactive({
  prop: 'last_service_time',
  order: 'descending'
})
const toTime = (value) => {
  const ms = new Date(value || '').getTime()
  return Number.isFinite(ms) ? ms : 0
}

const filteredCustomers = computed(() => {
  const typeFilter = activeTypeTab.value
  const baseList =
    typeFilter === 'all'
      ? customers.value
      : customers.value.filter((item) => {
          const t1 = (item?.customer_type || '').toString().trim()
          return t1 === typeFilter
        })
  const keyword = searchName.value.trim().toLowerCase()
  if (!keyword) {
    return baseList
  }
  return baseList.filter((item) => {
    const name = (item?.name || '').toString().toLowerCase()
    return name.includes(keyword)
  })
})

const sortedCustomers = computed(() => {
  const list = [...filteredCustomers.value]
  const { prop, order } = sortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'last_service_time') {
    return list.sort((a, b) => {
      const aTime = toTime(a?.last_service_time || a?.created_at)
      const bTime = toTime(b?.last_service_time || b?.created_at)
      return (aTime - bTime) * dir
    })
  }
  return list
})

const customerTotal = computed(() => (Array.isArray(sortedCustomers.value) ? sortedCustomers.value.length : 0))

const pagedCustomers = computed(() => {
  const list = Array.isArray(sortedCustomers.value) ? sortedCustomers.value : []
  const page = Number(customerPage.value) || 1
  const size = Number(customerPageSize.value) || 10
  const start = (page - 1) * size
  return list.slice(start, start + size)
})

watch(filteredCustomers, () => {
  customerPage.value = 1
})

const handleSortChange = ({ prop, order }) => {
  sortState.prop = prop || ''
  sortState.order = order
  customerPage.value = 1
}

const form = reactive({
  id: null,
  name: '',
  phone: '',
  address: '',
  email: '',
  customer_type: '',
  weekly_service_hours: null,
  weekly_served_hours: 0,
  gender: '',
  age: null,
  disability_type: '',
  ndis_number: '',
  aboriginal_torres_strait: false,
  ndis_funding_type: '',
  medicare_number: '',
  medicare_expiry: '',
  has_medical_card: false,
  medical_card_number: '',
  private_health_fund: '',
  private_policy_number: '',
  invoice_receiver_name: '',
  invoice_receiver_phone: '',
  invoice_receiver_email: '',
  invoice_receiver_address: '',
  emergency_contact1_name: '',
  emergency_contact1_phone: '',
  emergency_contact1_email: '',
  emergency_contact2_name: '',
  emergency_contact2_phone: '',
  emergency_contact2_email: '',
  introduction: '',
  notes: '',
  attachments: [],
  accepted_service_level1_ids: []
})

const validateMedicalCardNumber = (rule, value, callback) => {
  if (form.has_medical_card === true && (!value || !String(value).trim())) {
    callback(new Error(t('customer.medicalCardRequired')))
  } else {
    callback()
  }
}

const rules = computed(() => {
  const base = {
    name: [{ required: true, message: t('customer.nameRequired'), trigger: 'blur' }],
    phone: [{ required: true, message: t('customer.phoneRequired'), trigger: 'blur' }],
    address: [{ required: true, message: t('customer.addressRequired'), trigger: 'blur' }],
    email: [{ required: true, message: t('customer.emailRequired'), trigger: 'blur' }],
    customer_type: [{ required: true, message: t('customer.typeRequired'), trigger: 'change' }],
    weekly_service_hours: [{ required: true, message: t('customer.weeklyServiceHoursRequired'), trigger: 'change' }],
    gender: [{ required: true, message: t('customer.genderRequired'), trigger: 'change' }],
    age: [{ required: true, message: t('customer.ageRequired'), trigger: 'change' }],
    disability_type: [{ required: true, message: t('customer.disabilityTypeRequired'), trigger: 'blur' }],
    emergency_contact1_name: [{ required: true, message: t('customer.emergencyContact1NameRequired'), trigger: 'blur' }],
    emergency_contact1_phone: [{ required: true, message: t('customer.emergencyContact1PhoneRequired'), trigger: 'blur' }],
    emergency_contact1_email: [{ required: true, message: t('customer.emergencyContact1EmailRequired'), trigger: 'blur' }],
    introduction: [{ required: true, message: t('customer.introductionRequired'), trigger: 'blur' }],
    notes: [{ required: true, message: t('customer.notesRequired'), trigger: 'blur' }],
    medical_card_number: [{ validator: validateMedicalCardNumber, trigger: 'blur' }],
    accepted_service_level1_ids: [{ required: true, message: t('customer.acceptedServiceLevelRequired'), trigger: 'change' }]
  }

  base.ndis_number =
    form.customer_type === 'NDIS'
      ? [{ required: true, message: t('customer.ndisNumberRequired'), trigger: 'blur' }]
      : []

  return base
})

const loadCustomers = async () => {
  loading.value = true
  try {
    const params = {}
    params.customer_status = activeStatusTab.value
    if (activeTypeTab.value !== 'all') {
      params.customer_type = activeTypeTab.value
    }
    const list = await getCustomers(params)
    for (const item of list) {
      try {
        const docs = await getCustomerDocuments(item.id)
        item.hasAgreement = Array.isArray(docs) && docs.some(d => d.document_type === 'service_agreement')
      } catch {
        item.hasAgreement = false
      }
    }
    customers.value = list
  } catch (error) {
    ElMessage.error(t('customer.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleAdd = async () => {
  if (!serviceLevelOptions.value.length) {
    await loadServiceLevels()
  }
  Object.assign(form, {
    id: null,
    name: '',
    phone: '',
    address: '',
    email: '',
    customer_type: '',
    weekly_service_hours: null,
    weekly_served_hours: 0,
    gender: '',
    age: null,
    disability_type: '',
    ndis_number: '',
    aboriginal_torres_strait: false,
    ndis_funding_type: '',
    medicare_number: '',
    medicare_expiry: '',
    has_medical_card: false,
    medical_card_number: '',
    private_health_fund: '',
    private_policy_number: '',
    invoice_receiver_name: '',
    invoice_receiver_phone: '',
    invoice_receiver_email: '',
    invoice_receiver_address: '',
    emergency_contact1_name: '',
    emergency_contact1_phone: '',
    emergency_contact1_email: '',
    emergency_contact2_name: '',
    emergency_contact2_phone: '',
    emergency_contact2_email: '',
    introduction: '',
    notes: '',
    attachments: [],
    accepted_service_level1_ids: []
  })
  attachmentList.value = []
  ndisPlanFileList.value = []
  viewNdisPlanName.value = ''
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  if (!serviceLevelOptions.value.length) {
    await loadServiceLevels()
  }
  Object.assign(form, {
    id: row.id,
    name: row.name,
    phone: row.phone,
    address: row.address,
    email: row.email,
    customer_type: row.customer_type,
    weekly_service_hours: row.weekly_service_hours ?? null,
    weekly_served_hours: row.weekly_served_hours ?? 0,
    gender: row.gender,
    age: row.age,
    disability_type: row.disability_type,
    ndis_number: row.ndis_number || '',
    aboriginal_torres_strait: row.aboriginal_torres_strait || false,
    ndis_funding_type: row.ndis_funding_type || '',
    medicare_number: row.medicare_number || '',
    medicare_expiry: row.medicare_expiry || '',
    has_medical_card: row.has_medical_card || false,
    medical_card_number: row.medical_card_number || '',
    private_health_fund: row.private_health_fund || '',
    private_policy_number: row.private_policy_number || '',
    invoice_receiver_name: row.invoice_receiver_name || '',
    invoice_receiver_phone: row.invoice_receiver_phone || '',
    invoice_receiver_email: row.invoice_receiver_email || '',
    invoice_receiver_address: row.invoice_receiver_address || '',
    emergency_contact1_name: row.emergency_contact1_name || '',
    emergency_contact1_phone: row.emergency_contact1_phone || '',
    emergency_contact1_email: row.emergency_contact1_email || '',
    emergency_contact2_name: row.emergency_contact2_name || '',
    emergency_contact2_phone: row.emergency_contact2_phone || '',
    emergency_contact2_email: row.emergency_contact2_email || '',
    introduction: row.introduction,
    notes: row.notes,
    attachments: (row.attachments || []).map((item) => ({
      name: item.name,
      path: item.path
    })),
    accepted_service_level1_ids: row.accepted_service_level1_ids || row.accepted_service_level_ids || []
  })
  attachmentList.value = (row.attachments || []).map((item, index) => ({
    name: item.name,
    url: item.url,
    status: 'success',
    uid: `existing-${index}`,
    existing: true
  }))
  ndisPlanFileList.value = []
  viewNdisPlanName.value = row.ndis_plan_copy_path ? t('customer.ndisPlanUploaded') : ''
  dialogVisible.value = true
}

const handleView = (row) => {
  if (row?.has_update && row?.id) {
    markUpdatesRead('customer', row.id).catch(() => {})
    markUpdatesRead('customer_pending', row.id).catch(() => {})
    row.has_update = false
    try {
      window.dispatchEvent(new Event('updates-changed'))
    } catch {}
  }
  router.push(`/customers/${row.id}`)
}

const openUploadContract = (row) => {
  currentCustomerId.value = row.id
  uploadContractFileList.value = []
  selectedTemplateId.value = ''
  uploadContractMode.value = 'template'
  loadTemplates()
  uploadContractDialogVisible.value = true
}

const closeUploadContractDialog = () => {
  uploadContractDialogVisible.value = false
  uploadContractFileList.value = []
  selectedTemplateId.value = ''
  uploadContractMode.value = 'template'
}

const loadTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await getTemplateFiles()
    templateOptions.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } catch {
    templateOptions.value = []
  } finally {
    loadingTemplates.value = false
  }
}

const canSubmitUploadContract = computed(() => {
  if (!currentCustomerId.value) return false
  if (uploadContractMode.value === 'template') return !!selectedTemplateId.value
  return uploadContractFileList.value.length > 0
})

const submitUploadContract = async () => {
  if (!currentCustomerId.value) return
  try {
    if (uploadContractMode.value === 'template') {
      if (!selectedTemplateId.value) return
      await uploadCustomerContract(currentCustomerId.value, { templateId: selectedTemplateId.value })
    } else {
      const file = uploadContractFileList.value.find(f => f.raw)?.raw
      if (!file) return
      await uploadCustomerContract(currentCustomerId.value, { file })
    }
    ElMessage.success(t('customer.uploadContractSuccess'))
    closeUploadContractDialog()
    loadCustomers()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('customer.operationFailed'))
  }
}

const sendContract = async (row) => {
  if (!row.hasAgreement) {
    ElMessage.error(t('customer.needUploadFirst'))
    return
  }
  pendingSendContractRow.value = row
  sendContractLang.value = 'zh'
  sendContractDialogVisible.value = true
}

const submitSendContract = async () => {
  if (!pendingSendContractRow.value) return
  sendingContract.value = true
  try {
    const row = pendingSendContractRow.value
    await sendCustomerContract(row.id, row.email, sendContractLang.value)
    ElMessage.success(t('customer.sendSuccess'))
    sendContractDialogVisible.value = false
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('customer.sendFailed'))
  } finally {
    sendingContract.value = false
  }
}

const startReviewRow = async (row) => {
  if (!row?.hasAgreement) {
    ElMessage.error(t('customer.needUploadFirst'))
    return
  }
  try {
    await startArchiveReview(row.id)
    ElMessage.success(t('customer.startReviewSuccess'))
    loadCustomers()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('customer.operationFailed'))
  }
}

const viewSignedContract = async (row) => {
  try {
    const blob = await viewCustomerContract(row.id)
    const mime = (blob?.type || '').toLowerCase()
    const pdfLike = mime.includes('pdf') || mime === 'application/octet-stream' || mime === ''
    if (isMobile.value && pdfLike) {
      contractPreviewRow.value = row
      contractPreviewType.value = 'pdfjs'
      contractPreviewUrl.value = ''
      contractPreviewBlob.value = blob
      contractPreviewDialogVisible.value = true
      await nextTick()
      await renderContractPdfInDialog(blob)
      return
    }
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 5000)
  } catch {
    ElMessage.error(t('customer.operationFailed'))
  }
}

const renderContractPdfInDialog = async (blob) => {
  if (!contractPreviewPdfContainer.value || !contractPreviewPdfCanvasWrapper.value) return
  const canvasWrapper = contractPreviewPdfCanvasWrapper.value
  const key = `${contractPreviewRow.value?.id || ''}@@${blob?.size || 0}@@${blob?.type || ''}`
  if (contractPreviewPdfRenderedKey.value === key) return
  contractPreviewPdfRenderedKey.value = key
  canvasWrapper.innerHTML = ''

  const pdfjs = await loadPdfjs()
  const data = await blob.arrayBuffer()
  const pdf = await pdfjs.getDocument({ data, disableWorker: true }).promise
  const containerWidth = contractPreviewPdfContainer.value.clientWidth || 800
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

const closeContractPreview = () => {
  if (contractPreviewUrl.value && contractPreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(contractPreviewUrl.value)
  }
  contractPreviewDialogVisible.value = false
  contractPreviewType.value = ''
  contractPreviewUrl.value = ''
  contractPreviewRow.value = null
  contractPreviewBlob.value = null
  contractPreviewPdfRenderedKey.value = ''
  if (contractPreviewPdfCanvasWrapper.value) {
    contractPreviewPdfCanvasWrapper.value.innerHTML = ''
  }
}

const approveRow = async (row) => {
  try {
    await approveArchive(row.id)
    ElMessage.success(t('customer.approveSuccess'))
    loadCustomers()
  } catch {
    ElMessage.error(t('customer.operationFailed'))
  }
}

const rejectRow = async (row) => {
  try {
    await rejectArchive(row.id)
    ElMessage.success(t('customer.rejectSuccess'))
    loadCustomers()
  } catch {
    ElMessage.error(t('customer.operationFailed'))
  }
}

const deleteContractRow = async (row) => {
  try {
    await deleteCustomerContract(row.id)
    ElMessage.success(t('customer.deleteSuccess'))
    loadCustomers()
  } catch {
    ElMessage.error(t('customer.operationFailed'))
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('customer.deleteConfirm'), t('customer.tip'), { type: 'warning' })
    await deleteCustomer(row.id)
    ElMessage.success(t('customer.deleteSuccess'))
    loadCustomers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('customer.deleteFailed'))
    }
  }
}

const handleAttachmentChange = (file, fileList) => {
  attachmentList.value = fileList
}

const handleAttachmentRemove = (file, fileList) => {
  attachmentList.value = fileList
  if (file?.existing) {
    const index = form.attachments.findIndex((item) => item.name === file.name)
    if (index >= 0) {
      form.attachments.splice(index, 1)
    }
  }
}

const handleContractFileChange = (file, fileList) => {
  uploadContractFileList.value = fileList
}

const handleNdisPlanChange = (file, fileList) => {
  ndisPlanFileList.value = fileList
}

const handleNdisPlanRemove = () => {
  ndisPlanFileList.value = []
}

const handleSubmit = async () => {
  if (!formRef.value) return
  if (!HIDE_PHONY_CUSTOMER_FIELDS && form.has_medical_card === true && (!form.medical_card_number || !String(form.medical_card_number).trim())) {
    ElMessage.error(t('customer.medicalCardRequired'))
    return
  }
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const payload = {
          name: form.name,
          phone: form.phone,
          address: form.address,
          email: form.email,
          customer_type: form.customer_type,
          gender: form.gender,
          age: form.age,
          disability_type: form.disability_type,
          ndis_number: form.ndis_number || null,
          aboriginal_torres_strait: form.aboriginal_torres_strait || null,
          ndis_funding_type: form.ndis_funding_type || null,
          medicare_number: form.medicare_number || null,
          medicare_expiry: form.medicare_expiry || null,
          has_medical_card: form.has_medical_card === true,
          medical_card_number: form.has_medical_card === true ? (form.medical_card_number || null) : null,
          private_health_fund: form.private_health_fund || null,
          private_policy_number: form.private_policy_number || null,
          invoice_receiver_name: form.invoice_receiver_name || null,
          invoice_receiver_phone: form.invoice_receiver_phone || null,
          invoice_receiver_email: form.invoice_receiver_email || null,
          invoice_receiver_address: form.invoice_receiver_address || null,
          emergency_contact1_name: form.emergency_contact1_name || null,
          emergency_contact1_phone: form.emergency_contact1_phone || null,
          emergency_contact1_email: form.emergency_contact1_email || null,
          emergency_contact2_name: form.emergency_contact2_name || null,
          emergency_contact2_phone: form.emergency_contact2_phone || null,
          emergency_contact2_email: form.emergency_contact2_email || null,
          introduction: form.introduction,
          notes: form.notes,
          weekly_service_hours: form.weekly_service_hours,
          attachments: form.attachments,
          accepted_service_level1_ids: Array.isArray(form.accepted_service_level1_ids) ? form.accepted_service_level1_ids : []
        }
        if (form.id) {
          await updateCustomer(form.id, payload)
          const newFiles = attachmentList.value.filter((item) => item.raw)
          if (newFiles.length) {
            for (const item of newFiles) {
              await uploadCustomerAttachment(form.id, item.raw)
            }
          }
          const ndisFile = ndisPlanFileList.value.find((item) => item.raw)
          if (ndisFile?.raw && form.customer_type === 'NDIS') {
            await uploadNdisPlan(form.id, ndisFile.raw)
          }
          ElMessage.success(t('customer.updateSuccess'))
        } else {
          const created = await createCustomer(payload)
          const newFiles = attachmentList.value.filter((item) => item.raw)
          if (newFiles.length) {
            for (const item of newFiles) {
              await uploadCustomerAttachment(created.id, item.raw)
            }
          }
          const ndisFile = ndisPlanFileList.value.find((item) => item.raw)
          if (ndisFile?.raw && form.customer_type === 'NDIS') {
            await uploadNdisPlan(created.id, ndisFile.raw)
          }
          ElMessage.success(t('customer.createSuccess'))
        }
        dialogVisible.value = false
        loadCustomers()
      } catch (error) {
        ElMessage.error(t('customer.operationFailed'))
      }
    }
  })
}

onMounted(() => {
  syncStatusFromRoute()
  loadCustomers()
  loadServiceLevels()
  if (route.path.endsWith('/customers/pending')) {
    markPendingListReadIfNeeded()
  }
})

const statusTagType = (s) => {
  if (s === '未建档') return 'info'
  if (s === '待建档') return 'warning'
  if (s === '已建档') return 'success'
  return ''
}

// 支持后端状态筛选
watch(activeStatusTab, () => loadCustomers())
watch(activeTypeTab, () => loadCustomers())

const resolveStatusByPath = (path) => {
  if (path.endsWith('/customers/not-built')) return '未建档'
  if (path.endsWith('/customers/pending')) return '待建档'
  return '已建档'
}
const syncStatusFromRoute = () => {
  activeStatusTab.value = resolveStatusByPath(route.path)
}
watch(
  () => route.path,
  () => {
    const next = resolveStatusByPath(route.path)
    if (activeStatusTab.value !== next) activeStatusTab.value = next
    if (route.path.endsWith('/customers/pending')) {
      markPendingListReadIfNeeded()
    } else {
      pendingListMarkedRead.value = false
    }
  }
)

async function markPendingListReadIfNeeded() {
  if (pendingListMarkedRead.value) return
  pendingListMarkedRead.value = true
  try {
    await markUpdatesRead('customer_pending')
    try {
      window.dispatchEvent(new Event('updates-changed'))
    } catch {}
  } catch {}
}
</script>

<style scoped>
.customer-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
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

.ndis-plan-existing {
  margin-top: 8px;
  font-size: 13px;
  color: #909399;
}

.existing-attachments {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-tabs {
  margin-bottom: 12px;
}

.type-tabs {
  margin-bottom: 12px;
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

.pager-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
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
