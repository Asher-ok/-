<template>
  <div class="customer-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ $t('customer.customerDetail') }}</span>
          <div class="header-actions">
            <el-button v-if="canEdit" type="primary" @click="openEdit">{{ $t('customer.edit') }}</el-button>
            <el-tag :type="statusTagType(customer.customer_status || customer.status)" class="status-tag">{{ $t('customer.status') }}：{{ getCustomerStatusText(customer.customer_status || customer.status) }}</el-tag>
            <el-button @click="$router.back()">{{ $t('common.return') }}</el-button>
          </div>
        </div>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="$t('customer.basicInfo')" name="basic">
      <el-descriptions :column="isMobile ? 1 : 2" :direction="isMobile ? 'vertical' : 'horizontal'" border>
        <el-descriptions-item :label="$t('customer.name')">{{ customer.name }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.type')">{{ getCustomerTypeText(customer.customer_type) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.weeklyServiceHours')">{{ customer.weekly_service_hours != null ? Number(customer.weekly_service_hours).toFixed(2) : '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.weeklyServedHours')">{{ customer.weekly_served_hours != null ? Number(customer.weekly_served_hours).toFixed(2) : '0.00' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.acceptedServiceLevel')" :span="2">
          <span v-if="Array.isArray(customer.accepted_service_level1_names) && customer.accepted_service_level1_names.length">
            {{ customer.accepted_service_level1_names.join(', ') }}
          </span>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('customer.gender')">{{ getGenderText(customer.gender) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.age')">{{ customer.age != null ? customer.age : '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.disabilityType')">{{ customer.disability_type || '-' }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.phone')">{{ customer.phone }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.email')">{{ customer.email }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.address')" :span="2">{{ customer.address }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.emergencyContactSection')" :span="2">{{ formatEmergencyContact(1) }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.emergencyContact2Section')" :span="2">{{ formatEmergencyContact(2) }}</el-descriptions-item>
        <template v-if="customer.customer_type === 'NDIS'">
          <el-descriptions-item :label="$t('customer.ndisNumber')">{{ customer.ndis_number || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.ndisFundingType')">{{ customer.ndis_funding_type || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.aboriginalTorresStrait')">{{ customer.aboriginal_torres_strait ? $t('common.yes') : $t('common.no') }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.ndisPlanFile')">
            <el-link v-if="customer.ndis_plan_copy_path" type="primary" @click="handleDownloadNdisPlan">
              {{ $t('customer.downloadNdisPlan') }}
            </el-link>
            <span v-else>{{ $t('customer.ndisPlanNotUploaded') }}</span>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('customer.hasMedicalCard')">{{ customer.has_medical_card === true ? $t('common.yes') : $t('common.no') }}</el-descriptions-item>
          <el-descriptions-item v-if="customer.has_medical_card === true" :label="$t('customer.medicalCardNumber')">{{ customer.medical_card_number || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.medicareNumber')">{{ customer.medicare_number || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.medicareExpiry')">{{ customer.medicare_expiry || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.privateHealthFund')">{{ customer.private_health_fund || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.privatePolicyNumber')">{{ customer.private_policy_number || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.invoiceReceiverName')">{{ customer.invoice_receiver_name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.invoiceReceiverPhone')">{{ customer.invoice_receiver_phone || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.invoiceReceiverEmail')">{{ customer.invoice_receiver_email || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('customer.invoiceReceiverAddress')" :span="2">{{ customer.invoice_receiver_address || '-' }}</el-descriptions-item>
        </template>
        <el-descriptions-item :label="$t('customer.introduction')" :span="2">{{ customer.introduction }}</el-descriptions-item>
        <el-descriptions-item :label="$t('customer.notes')" :span="2">{{ customer.notes }}</el-descriptions-item>
      </el-descriptions>
        </el-tab-pane>
        <el-tab-pane :label="$t('customerDoc.tabTitle')" name="documents">
          <CustomerDocumentManager :customer-id="customerId" />
        </el-tab-pane>
        <el-tab-pane :label="$t('menu.tasks')" name="tasks">
          <div class="embedded-pane">
            <div class="filter-bar">
              <el-select v-model="taskFilterStatus" :placeholder="$t('task.filterStatus')" clearable style="width: 150px">
                <el-option :label="$t('task.pending')" value="pending" />
                <el-option :label="$t('task.inProgress')" value="in_progress" />
                <el-option :label="$t('task.completed')" value="completed" />
                <el-option :label="$t('task.rejected')" value="rejected" />
                <el-option :label="$t('task.approved')" value="approved" />
                <el-option :label="$t('task.cancelled')" value="cancelled" />
              </el-select>
              <el-select v-model="taskSearchField" :placeholder="$t('task.searchCondition')" clearable style="width: 150px">
                <el-option :label="$t('task.assignedEmployee')" value="assigned_employee" />
                <el-option :label="$t('task.title')" value="title" />
              </el-select>
              <el-select v-model="taskSearchValue" :placeholder="$t('task.enterKeyword')" clearable filterable style="width: 240px" :disabled="!taskSearchField">
                <el-option v-for="opt in customerTaskSearchOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
              <el-button type="primary" @click="applyCustomerTaskSearch">{{ $t('task.search') }}</el-button>
              <el-button @click="resetCustomerTaskSearch">{{ $t('task.reset') }}</el-button>
            </div>

            <el-table :data="customerTaskPagedRows" v-loading="customerTaskLoading" stripe table-layout="auto" style="width: 100%">
              <el-table-column prop="status" :label="$t('task.status')" min-width="160">
                <template #default="{ row }">
                  <el-tag :type="getTaskStatusType(row.status)">{{ getTaskStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="title" :label="$t('task.title')" min-width="260">
                <template #default="{ row }">
                  <el-link type="primary" class="clickable-text" :underline="true" @click="goTaskDetail(row)">{{ row.title || '-' }}</el-link>
                </template>
              </el-table-column>
              <el-table-column :label="$t('task.serviceItem')" min-width="350">
                <template #default="{ row }">
                  <el-tooltip v-if="getCustomerTaskServiceCodes(row).length" :content="getCustomerTaskServiceCodes(row).join(', ')" placement="top">
                    <span>{{ getCustomerTaskServiceCodes(row)[0] }}</span>
                  </el-tooltip>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column :label="$t('task.serviceStartTime')" min-width="280">
                <template #default="{ row }">
                  <span>{{ getCustomerTaskServiceStartTime(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column :label="$t('task.serviceEndTime')" min-width="280">
                <template #default="{ row }">
                  <span>{{ getCustomerTaskServiceEndTime(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column :label="$t('task.assignedEmployeeLabel')" width="170">
                <template #default="{ row }">
                  <span>{{ getCustomerTaskAssignedEmployeeName(row) }}</span>
                </template>
              </el-table-column>
              <el-table-column v-if="taskFilterStatus === 'pending'" :label="$t('task.overdueTime')" width="190">
                <template #default="{ row }">
                  <span>{{ calculateCustomerTaskOverdueDuration(row) || '-' }}</span>
                </template>
              </el-table-column>
            </el-table>

            <div class="pager-bar">
              <el-pagination
                v-model:current-page="customerTaskPage"
                v-model:page-size="customerTaskPageSize"
                :page-sizes="[10]"
                layout="total, prev, pager, next"
                :total="customerTaskTotal"
              />
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane :label="$t('menu.invoices')" name="invoices">
          <div class="embedded-pane">
            <el-tabs v-model="customerInvoiceTab">
              <el-tab-pane :label="$t('invoice.issuedTab')" name="issued">
                <div class="filter-bar">
                  <el-select v-model="customerInvoiceStatus" :placeholder="$t('common.selectStatus')" clearable style="width: 180px" @change="loadCustomerIssuedInvoices">
                    <el-option :label="getInvoiceStatusText('draft')" value="draft" />
                    <el-option :label="getInvoiceStatusText('sent')" value="sent" />
                    <el-option :label="getInvoiceStatusText('paid')" value="paid" />
                    <el-option :label="getInvoiceStatusText('cancelled')" value="cancelled" />
                  </el-select>
                  <el-button @click="loadCustomerIssuedInvoices">{{ $t('common.refresh') }}</el-button>
                </div>

                <el-table :data="customerIssuedInvoicePagedRows" v-loading="customerIssuedLoading" stripe table-layout="auto" style="width: 100%">
                  <el-table-column prop="invoice_number" :label="$t('invoice.invoiceNumber')" min-width="240">
                    <template #default="{ row }">
                      <el-link type="primary" class="clickable-text" :underline="true" @click="goInvoiceDetail(row)">{{ row.invoice_number || '-' }}</el-link>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('invoice.invoiceDate')" min-width="200">
                    <template #default="{ row }">
                      {{ formatDate(row.invoice_date, 'YYYY-MM-DD') }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="total_amount" :label="$t('invoice.totalAmount')" min-width="200">
                    <template #default="{ row }">
                      ${{ formatAmountNumber(row.total_amount) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" :label="$t('invoice.status')" min-width="160">
                    <template #default="{ row }">
                      <el-tag :type="getInvoiceStatusType(row.status)">{{ getInvoiceStatusText(row.status) }}</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('invoice.operations')" width="240" :fixed="isMobile ? false : 'right'" align="right" header-align="left">
                    <template #default="{ row }">
                      <div class="action-buttons action-buttons--scroll">
                        <div class="action-buttons-inner">
                          <el-button type="success" size="small" @click="handleCustomerInvoiceEdit(row)">{{ $t('invoice.edit') }}</el-button>
                          <el-button
                            v-if="row.pdf_url && (row.status === 'draft' || row.status === 'sent' || row.status === 'paid')"
                            type="warning"
                            size="small"
                            @click="handleCustomerInvoiceSend(row)"
                          >
                            {{ $t('invoice.send') }}
                          </el-button>
                          <el-button type="danger" size="small" @click="handleCustomerInvoiceDelete(row)">{{ $t('common.delete') }}</el-button>
                        </div>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>

                <div class="pager-bar">
                  <el-pagination
                    v-model:current-page="customerIssuedInvoicePage"
                    v-model:page-size="customerIssuedInvoicePageSize"
                    :page-sizes="[10]"
                    layout="total, prev, pager, next"
                    :total="customerIssuedInvoiceTotal"
                  />
                </div>
              </el-tab-pane>
              <el-tab-pane :label="$t('invoice.unissuedTab')" name="unissued">
                <div class="filter-bar">
                  <el-button @click="loadCustomerUnissuedTasks" :loading="customerUnissuedLoading">{{ $t('common.refresh') }}</el-button>
                </div>

                <el-table :data="customerUnissuedPagedRows" v-loading="customerUnissuedLoading" stripe>
                  <el-table-column prop="title" :label="$t('task.title')" min-width="180" />
                  <el-table-column :label="$t('task.assignedEmployeeLabel')" min-width="160">
                    <template #default="{ row }">
                      <span>{{ row.assigned_employee?.name || row.employee?.name || row.assigned_employee_name || row.employee_name || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('task.serviceItem')" min-width="160">
                    <template #default="{ row }">
                      <el-tooltip v-if="getUnissuedServiceCodes(row).length" :content="getUnissuedServiceCodes(row).join(', ')" placement="top">
                        <span>{{ getUnissuedServiceCodes(row)[0] }}</span>
                      </el-tooltip>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('invoice.totalAmount')" width="140">
                    <template #default="{ row }">
                      <span>${{ formatAmountNumber(getUnissuedTotalAmount(row)) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('invoice.operations')" width="180" :fixed="isMobile ? false : 'right'">
                    <template #default="{ row }">
                      <el-button type="primary" size="small" @click="openUnissuedGenerate(row)">{{ $t('invoice.generateInvoice') }}</el-button>
                    </template>
                  </el-table-column>
                </el-table>

                <div class="pager-bar">
                  <el-pagination
                    v-model:current-page="customerUnissuedPage"
                    v-model:page-size="customerUnissuedPageSize"
                    :page-sizes="[10]"
                    layout="total, prev, pager, next"
                    :total="customerUnissuedTotal"
                  />
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog v-model="editDialogVisible" :title="$t('customer.editCustomer')" width="760px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="auto">
        <el-form-item :label="$t('customer.name')" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item :label="$t('customer.phone')" prop="phone">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item :label="$t('customer.email')">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item :label="$t('customer.address')" prop="address">
          <el-input v-model="editForm.address" />
        </el-form-item>
        <el-form-item :label="$t('customer.type')" prop="customer_type">
          <el-select v-model="editForm.customer_type" :placeholder="$t('customer.selectType')">
            <el-option :label="$t('customer.elderly')" value="养老" />
            <el-option :label="$t('customer.disability')" value="助残" />
            <el-option :label="$t('customer.ndis')" value="NDIS" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('customer.weeklyServiceHours')" prop="weekly_service_hours">
          <el-input-number v-model="editForm.weekly_service_hours" :min="0" :precision="2" :step="0.5" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="$t('customer.acceptedServiceLevel')">
          <el-select
            v-model="editForm.accepted_service_level1_ids"
            multiple
            filterable
            collapse-tags
            :placeholder="$t('customer.selectAcceptedServiceLevel')"
            style="width: 100%"
          >
            <el-option v-for="opt in serviceLevelOptions" :key="opt.id" :label="opt.name" :value="opt.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('customer.gender')">
          <el-select v-model="editForm.gender" :placeholder="$t('customer.selectGender')">
            <el-option :label="$t('customer.male')" value="男" />
            <el-option :label="$t('customer.female')" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('customer.age')">
          <el-input-number v-model="editForm.age" :min="0" :max="120" />
        </el-form-item>
        <el-form-item :label="$t('customer.disabilityType')">
          <el-input v-model="editForm.disability_type" />
        </el-form-item>
        <el-divider content-position="left">{{ $t('customer.emergencyContactSection') }}</el-divider>
        <el-form-item :label="$t('customer.emergencyContact1Name')">
          <el-input v-model="editForm.emergency_contact1_name" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact1Phone')">
          <el-input v-model="editForm.emergency_contact1_phone" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact1Email')">
          <el-input v-model="editForm.emergency_contact1_email" />
        </el-form-item>
        <el-divider content-position="left">{{ $t('customer.emergencyContact2Section') }}</el-divider>
        <el-form-item :label="$t('customer.emergencyContact2Name')">
          <el-input v-model="editForm.emergency_contact2_name" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact2Phone')">
          <el-input v-model="editForm.emergency_contact2_phone" />
        </el-form-item>
        <el-form-item :label="$t('customer.emergencyContact2Email')">
          <el-input v-model="editForm.emergency_contact2_email" />
        </el-form-item>
        <el-form-item :label="$t('customer.introduction')">
          <el-input v-model="editForm.introduction" type="textarea" />
        </el-form-item>
        <el-form-item :label="$t('customer.notes')">
          <el-input v-model="editForm.notes" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="editSaving" @click="submitEdit">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="unissuedDialogVisible" :title="$t('invoice.generateInvoice')" width="900px" :close-on-click-modal="false">
      <div v-loading="unissuedPreviewLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('invoice.customer')">{{ unissuedPreview.customerName }}</el-descriptions-item>
          <el-descriptions-item :label="$t('task.assignedEmployeeLabel')">{{ unissuedPreview.employeeName }}</el-descriptions-item>
          <el-descriptions-item :label="$t('invoice.invoiceDate')">{{ unissuedPreview.invoiceDate }}</el-descriptions-item>
          <el-descriptions-item :label="$t('invoice.totalAmount')">${{ formatAmountNumber(unissuedPreview.totalAmount) }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>{{ $t('invoice.invoiceItems') }}</el-divider>
        <el-table :data="unissuedPreview.items" stripe>
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
        <el-button @click="unissuedDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="unissuedGenerating" @click="confirmUnissuedGenerate">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="invoiceEditDialogVisible" :title="$t('invoice.editInvoice')" width="900px" :close-on-click-modal="false">
      <el-form :model="invoiceEditForm" :rules="invoiceEditRules" ref="invoiceEditFormRef" label-width="120px" v-loading="invoiceEditLoading">
        <el-form-item :label="$t('invoice.invoiceNumber')">
          <el-input v-model="invoiceEditForm.invoice_number" disabled />
        </el-form-item>
        <el-form-item :label="$t('invoice.customer')">
          <el-input :model-value="customer.name || '-'" disabled />
        </el-form-item>
        <el-form-item :label="$t('invoice.invoiceDate')" prop="invoice_date">
          <el-date-picker v-model="invoiceEditForm.invoice_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>

        <el-divider>{{ $t('invoice.invoiceItems') }}</el-divider>
        <div class="edit-items-toolbar">
          <el-button type="primary" plain size="small" @click="addInvoiceEditItem">{{ $t('invoice.addItem') }}</el-button>
        </div>
        <el-table :data="invoiceEditForm.items" stripe>
          <el-table-column :label="$t('invoice.description')" min-width="180">
            <template #default="{ row }">
              <el-input v-model="row.description" />
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceCode')" min-width="140">
            <template #default="{ row }">
              <el-input v-model="row.service_code" />
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.unitPrice')" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.price" :min="0.01" :precision="2" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceDuration')" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.quantity" :min="0.01" :precision="2" controls-position="right" />
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.totalPrice')" width="120">
            <template #default="{ row }">
              <span class="item-amount">${{ formatAmountNumber(Number(row.price || 0) * Number(row.quantity || 0)) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceDate')" width="140">
            <template #default="{ row }">
              <el-date-picker v-model="row.service_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceTimeStart')" width="140">
            <template #default="{ row }">
              <el-input v-model="row.service_time_start" placeholder="0900" />
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceTimeEnd')" width="140">
            <template #default="{ row }">
              <el-input v-model="row.service_time_end" placeholder="1200" />
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.operations')" width="100" :fixed="isMobile ? false : 'right'">
            <template #default="{ $index }">
              <el-button type="danger" size="small" @click="removeInvoiceEditItem($index)">{{ $t('invoice.removeItem') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="invoiceEditDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="invoiceEditSaving" @click="submitInvoiceEdit">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="invoiceSendLangDialogVisible" :title="$t('invoice.send')" width="360px">
      <el-form label-width="80px">
        <el-form-item label="语言">
          <el-select v-model="invoiceSendLang" style="width: 100%">
            <el-option label="中文" value="zh" />
            <el-option label="English" value="en" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="invoiceSendLangDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="invoiceSending" @click="submitCustomerInvoiceSend">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, inject, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCustomer, updateCustomer, downloadNdisPlan } from '@/api/customers'
import { getTasks } from '@/api/tasks'
import { getEmployees } from '@/api/employees'
import { getServiceLevel1, getInvoices, getInvoice, getTasksForInvoice, getInvoiceTaskDetail, generateInvoiceForTask, updateInvoice, sendInvoice, deleteInvoice } from '@/api/invoices'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import CustomerDocumentManager from './CustomerDocumentManager.vue'
import { markUpdatesRead } from '@/api/updates'
import { formatDate, formatDateTimeToMinute } from '@/utils/formatters'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))
const activeTab = ref('basic')
const route = useRoute()
const router = useRouter()
const customerId = route.params.id
const customer = ref({})
const loading = ref(false)
const editDialogVisible = ref(false)
const editSaving = ref(false)
const editFormRef = ref(null)
const serviceLevelOptions = ref([])
const employees = ref([])

const customerTaskLoading = ref(false)
const customerTaskAllRows = ref([])
const customerTaskPage = ref(1)
const customerTaskPageSize = ref(10)
const taskFilterStatus = ref('')
const taskSearchField = ref('')
const taskSearchValue = ref('')

const customerInvoiceTab = ref('issued')
const customerInvoiceStatus = ref('')
const customerIssuedLoading = ref(false)
const customerIssuedInvoices = ref([])
const customerIssuedInvoicePage = ref(1)
const customerIssuedInvoicePageSize = ref(10)

const customerUnissuedLoading = ref(false)
const customerUnissuedTasks = ref([])
const customerUnissuedPage = ref(1)
const customerUnissuedPageSize = ref(10)

const unissuedDialogVisible = ref(false)
const unissuedPreviewLoading = ref(false)
const unissuedGenerating = ref(false)
const unissuedCurrentTask = ref(null)
const unissuedPreview = ref({
  customerId: '',
  customerName: '',
  employeeId: '',
  employeeName: '',
  invoiceDate: '',
  items: [],
  totalAmount: 0
})

const invoiceEditDialogVisible = ref(false)
const invoiceEditLoading = ref(false)
const invoiceEditSaving = ref(false)
const invoiceEditFormRef = ref(null)
const invoiceEditForm = reactive({
  id: '',
  invoice_number: '',
  invoice_date: '',
  items: []
})

const invoiceEditRules = {
  invoice_date: [{ required: true, message: t('invoice.invoiceDateRequired'), trigger: 'change' }]
}

const invoiceSendLangDialogVisible = ref(false)
const invoiceSendLang = ref('en')
const invoiceSending = ref(false)
const pendingSendInvoiceRow = ref(null)

const canEdit = computed(() => {
  const s = customer.value?.customer_status || customer.value?.status
  return s === '未建档' || s === '待建档'
})

const getCustomerStatusText = (status) => {
  const s = (status || '').toString().trim()
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

const getGenderText = (gender) => {
  const g = (gender || '').toString().trim()
  if (!g) return '-'
  const map = {
    男: t('customer.male'),
    女: t('customer.female'),
  }
  return map[g] || g
}

const editForm = reactive({
  name: '',
  phone: '',
  email: '',
  address: '',
  customer_type: '',
  weekly_service_hours: null,
  gender: '',
  age: null,
  disability_type: '',
  introduction: '',
  notes: '',
  accepted_service_level1_ids: [],
  emergency_contact1_name: '',
  emergency_contact1_phone: '',
  emergency_contact1_email: '',
  emergency_contact2_name: '',
  emergency_contact2_phone: '',
  emergency_contact2_email: ''
})

const editRules = {
  name: [{ required: true, message: t('customer.nameRequired'), trigger: 'blur' }],
  phone: [{ required: true, message: t('customer.phoneRequired'), trigger: 'blur' }],
  address: [{ required: true, message: t('customer.addressRequired'), trigger: 'blur' }],
  weekly_service_hours: [{ required: true, message: t('customer.weeklyServiceHoursRequired'), trigger: 'change' }]
}

const loadServiceLevels = async () => {
  try {
    const res = await getServiceLevel1()
    const rows = Array.isArray(res) ? res : (Array.isArray(res?.data) ? res.data : (Array.isArray(res?.items) ? res.items : []))
    serviceLevelOptions.value = rows.map((r) => ({ id: r.id, name: r.name })).filter((i) => i.id && i.name)
  } catch (e) {
    serviceLevelOptions.value = []
  }
}

const handleDownloadNdisPlan = async () => {
  try {
    const response = await downloadNdisPlan(customerId)
    const blob = response instanceof Blob ? response : response.data
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `ndis_plan_${customer.value.name || customerId}.pdf`
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 3000)
  } catch (error) {
    ElMessage.error(t('customer.downloadFailed'))
  }
}

const loadCustomer = async () => {
  loading.value = true
  try {
    customer.value = await getCustomer(customerId)
  } catch (error) {
    ElMessage.error(t('customer.loadFailed'))
  } finally {
    loading.value = false
  }
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

const normalizeString = (value) => (value == null ? '' : String(value)).trim()

const loadEmployees = async () => {
  try {
    employees.value = await getEmployees()
  } catch {
    employees.value = []
  }
}

const formatAmountNumber = (num) => {
  const n = Number(num || 0)
  return n.toFixed(2)
}

const getTaskStatusType = (status) => {
  const map = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    rejected: 'danger',
    approved: 'success',
    cancelled: 'danger'
  }
  return map[status] || ''
}

const getTaskStatusText = (status) => {
  const map = {
    pending: t('task.pending'),
    in_progress: t('task.inProgress'),
    completed: t('task.completed'),
    rejected: t('task.rejected'),
    approved: t('task.approved'),
    cancelled: t('task.cancelled')
  }
  return map[status] || status
}

const getCustomerTaskServiceCodes = (row) => {
  const rawList = Array.isArray(row?.services)
    ? row.services
    : (Array.isArray(row?.service_items) ? row.service_items : (Array.isArray(row?.serviceItems) ? row.serviceItems : []))
  const codes = rawList
    .map((s) => s?.service_code || s?.code || s?.serviceCode || '')
    .map((s) => normalizeString(s))
    .filter(Boolean)
  if (!codes.length) {
    const fallback = normalizeString(row?.service_code || '')
    if (fallback) codes.push(fallback)
  }
  return Array.from(new Set(codes))
}

const getCustomerTaskServiceStartTime = (row) => {
  if (row?.service_start_time || row?.service_time) return formatDateTimeToMinute(row.service_start_time || row.service_time)
  const list = Array.isArray(row?.services) ? row.services : (Array.isArray(row?.service_items) ? row.service_items : [])
  const times = list.map((s) => s?.service_time_start || s?.service_start_time).filter(Boolean)
  if (!times.length) return '-'
  const sorted = [...times].sort()
  return formatDateTimeToMinute(sorted[0])
}

const getCustomerTaskServiceEndTime = (row) => {
  if (row?.service_end_time) return formatDateTimeToMinute(row.service_end_time)
  const list = Array.isArray(row?.services) ? row.services : (Array.isArray(row?.service_items) ? row.service_items : [])
  const times = list.map((s) => s?.service_time_end || s?.service_end_time).filter(Boolean)
  if (!times.length) return '-'
  const sorted = [...times].sort()
  return formatDateTimeToMinute(sorted[sorted.length - 1])
}

const getCustomerTaskAssignedEmployeeName = (row) => {
  const id = row?.assigned_employee_id || row?.assigned_employee?.id || ''
  if (!id) return t('task.allEmployees')
  const matched = (employees.value || []).find((e) => e.id === id)
  return matched?.name || row?.assigned_employee?.name || row?.assigned_employee_name || t('task.allEmployees')
}

const calculateCustomerTaskOverdueDuration = (row) => {
  if (row?.overdue_duration) return row.overdue_duration
  if (!row?.latest_claim_time) return null
  if (row?.status !== 'pending') return null
  const now = new Date()
  const claimTime = new Date(row.latest_claim_time)
  if (Number.isNaN(claimTime.getTime())) return null
  if (claimTime >= now) return null
  const diff = now - claimTime
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  if (days > 0) return `${t('task.overdue')} ${days}天${hours}小时`
  if (hours > 0) return `${t('task.overdue')} ${hours}小时${minutes}分钟`
  return `${t('task.overdue')} ${minutes}分钟`
}

const goTaskDetail = (row) => {
  const id = row?.id || row?.task_id || row?.taskId
  if (!id) return
  router.push(`/tasks/${id}`)
}

const parseSortTime = (value) => {
  const s = normalizeString(value)
  if (!s || s === '-') return 0
  const d = new Date(s.includes('T') ? s : s.replace(' ', 'T'))
  const n = d.getTime()
  return Number.isNaN(n) ? 0 : n
}

const customerTaskFilteredSorted = computed(() => {
  let rows = Array.isArray(customerTaskAllRows.value) ? customerTaskAllRows.value : []
  if (taskFilterStatus.value) rows = rows.filter((r) => r?.status === taskFilterStatus.value)
  const f = normalizeString(taskSearchField.value)
  const v = normalizeString(taskSearchValue.value)
  if (f && v) {
    if (f === 'title') {
      rows = rows.filter((r) => normalizeString(r?.title).includes(v))
    } else if (f === 'assigned_employee') {
      rows = rows.filter((r) => {
        const id = r?.assigned_employee_id || r?.assigned_employee?.id || ''
        const matched = id ? (employees.value || []).find((e) => e.id === id) : null
        const name = normalizeString(matched?.name || r?.assigned_employee?.name || r?.assigned_employee_name || '')
        const num = normalizeString(matched?.employee_number || '')
        return name.includes(v) || (num && num.includes(v))
      })
    }
  }
  const sorted = [...rows].sort((a, b) => {
    const at = parseSortTime(a?.service_start_time || a?.service_time) || parseSortTime(getCustomerTaskServiceStartTime(a))
    const bt = parseSortTime(b?.service_start_time || b?.service_time) || parseSortTime(getCustomerTaskServiceStartTime(b))
    return bt - at
  })
  return sorted
})

const customerTaskTotal = computed(() => customerTaskFilteredSorted.value.length)

const customerTaskPagedRows = computed(() => {
  const page = Number(customerTaskPage.value) || 1
  const size = Number(customerTaskPageSize.value) || 10
  const start = (page - 1) * size
  return customerTaskFilteredSorted.value.slice(start, start + size)
})

const customerTaskSearchOptions = computed(() => {
  const f = normalizeString(taskSearchField.value)
  const rows = Array.isArray(customerTaskAllRows.value) ? customerTaskAllRows.value : []
  if (!f) return []
  if (f === 'title') {
    const titles = rows.map((r) => normalizeString(r?.title)).filter(Boolean)
    const uniq = Array.from(new Set(titles)).sort((a, b) => a.localeCompare(b))
    return uniq.map((s) => ({ label: s, value: s }))
  }
  if (f === 'assigned_employee') {
    const employeeById = new Map((employees.value || []).map((e) => [e.id, e]))
    const ids = rows.map((r) => r?.assigned_employee_id).filter(Boolean)
    const uniqIds = Array.from(new Set(ids))
    const opts = uniqIds
      .map((id) => {
        const emp = employeeById.get(id)
        const name = normalizeString(emp?.name || '')
        const num = normalizeString(emp?.employee_number || '')
        const label = name && num ? `${name}（${num}）` : (name || num)
        const value = num || name
        return label && value ? { label, value } : null
      })
      .filter(Boolean)
    opts.sort((a, b) => a.label.localeCompare(b.label))
    return opts
  }
  return []
})

const applyCustomerTaskSearch = () => {
  customerTaskPage.value = 1
}

const resetCustomerTaskSearch = () => {
  taskFilterStatus.value = ''
  taskSearchField.value = ''
  taskSearchValue.value = ''
  customerTaskPage.value = 1
}

watch([taskFilterStatus, taskSearchField, taskSearchValue], () => {
  customerTaskPage.value = 1
  if (!taskSearchField.value) taskSearchValue.value = ''
})

const loadCustomerTasks = async () => {
  customerTaskLoading.value = true
  try {
    const rows = await getTasks()
    const list = Array.isArray(rows) ? rows : getArrayFromResponse(rows)
    customerTaskAllRows.value = list.filter((r) => {
      const cid = r?.customer_id || r?.customer?.id || ''
      return cid === customerId
    })
  } catch {
    customerTaskAllRows.value = []
  } finally {
    customerTaskLoading.value = false
  }
}

const getInvoiceStatusType = (status) => {
  const map = {
    draft: 'info',
    sent: 'warning',
    paid: 'success',
    cancelled: 'danger'
  }
  return map[status] || ''
}

const getInvoiceStatusText = (status) => {
  const map = {
    draft: t('invoice.draft'),
    sent: t('invoice.sent'),
    paid: t('invoice.paid'),
    cancelled: t('invoice.cancelled')
  }
  return map[status] || status
}

const loadCustomerIssuedInvoices = async () => {
  customerIssuedLoading.value = true
  try {
    const res = await getInvoices(customerId, customerInvoiceStatus.value || null)
    customerIssuedInvoices.value = getArrayFromResponse(res)
  } catch {
    customerIssuedInvoices.value = []
  } finally {
    customerIssuedLoading.value = false
  }
}

const customerIssuedInvoiceTotal = computed(() => (Array.isArray(customerIssuedInvoices.value) ? customerIssuedInvoices.value.length : 0))

const customerIssuedInvoicePagedRows = computed(() => {
  const list = Array.isArray(customerIssuedInvoices.value) ? customerIssuedInvoices.value : []
  const page = Number(customerIssuedInvoicePage.value) || 1
  const size = Number(customerIssuedInvoicePageSize.value) || 10
  const start = (page - 1) * size
  return list.slice(start, start + size)
})

watch([customerInvoiceStatus], () => {
  customerIssuedInvoicePage.value = 1
})

const goInvoiceDetail = (row) => {
  const id = row?.id || row?.invoice_id || row?.invoiceId
  if (!id) return
  router.push(`/invoices/${id}`)
}

const addInvoiceEditItem = () => {
  invoiceEditForm.items.push({
    id: '',
    task_id: '',
    description: '',
    service_code: '',
    price: 0,
    quantity: 1,
    service_date: '',
    service_time_start: '',
    service_time_end: ''
  })
}

const removeInvoiceEditItem = (index) => {
  invoiceEditForm.items.splice(index, 1)
}

const handleCustomerInvoiceEdit = async (row) => {
  const id = row?.id || row?.invoice_id || row?.invoiceId
  if (!id) return
  invoiceEditLoading.value = true
  try {
    const invoice = await getInvoice(id)
    invoiceEditForm.id = invoice.id
    invoiceEditForm.invoice_number = invoice.invoice_number
    invoiceEditForm.invoice_date = invoice.invoice_date ? formatDate(invoice.invoice_date, 'YYYY-MM-DD') : ''
    invoiceEditForm.items = (invoice.items || []).map((item) => ({
      id: item.id,
      task_id: item.task_id || '',
      description: item.description || '',
      service_code: item.service_code || '',
      price: Number(item.price || 0),
      quantity: Number(item.quantity || 0),
      service_date: item.service_date ? formatDate(item.service_date, 'YYYY-MM-DD') : '',
      service_time_start: item.service_time_start || '',
      service_time_end: item.service_time_end || ''
    }))
    if (!invoiceEditForm.items.length) {
      addInvoiceEditItem()
    }
    invoiceEditDialogVisible.value = true
  } catch (error) {
    const errorMessage = error?.response?.data?.detail || error?.message || t('invoice.loadInvoiceFailed')
    ElMessage.error(errorMessage)
  } finally {
    invoiceEditLoading.value = false
  }
}

const submitInvoiceEdit = async () => {
  if (!invoiceEditFormRef.value) return
  await invoiceEditFormRef.value.validate(async (valid) => {
    if (!valid) return
    if (!invoiceEditForm.items.length) {
      ElMessage.error(t('invoice.itemRequired'))
      return
    }
    const missingDesc = invoiceEditForm.items.find((item) => !item.description)
    if (missingDesc) {
      ElMessage.error(t('invoice.itemInvalid'))
      return
    }
    const invalidPriceQty = invoiceEditForm.items.find(
      (item) => Number(item.price || 0) <= 0 || Number(item.quantity || 0) <= 0
    )
    if (invalidPriceQty) {
      ElMessage.error(t('invoice.priceQuantityRequired'))
      return
    }

    try {
      invoiceEditSaving.value = true
      const payload = {
        customer_id: customerId,
        invoice_date: invoiceEditForm.invoice_date ? `${invoiceEditForm.invoice_date}T00:00:00.000Z` : null,
        items: invoiceEditForm.items.map((item) => ({
          task_id: item.task_id || null,
          description: item.description,
          service_code: item.service_code || null,
          price: item.price || 0,
          quantity: item.quantity || 0,
          service_date: item.service_date ? `${item.service_date}T00:00:00.000Z` : null,
          service_time_start: item.service_time_start || null,
          service_time_end: item.service_time_end || null
        }))
      }
      await updateInvoice(invoiceEditForm.id, payload)
      ElMessage.success(t('invoice.editSuccess'))
      invoiceEditDialogVisible.value = false
      await loadCustomerIssuedInvoices()
    } catch (error) {
      const errorMessage = error?.response?.data?.detail || error?.message || t('invoice.editFailed')
      ElMessage.error(errorMessage)
    } finally {
      invoiceEditSaving.value = false
    }
  })
}

const handleCustomerInvoiceSend = (row) => {
  if (!row?.pdf_url) {
    ElMessage.warning(t('invoice.fileNotExists'))
    return
  }
  pendingSendInvoiceRow.value = row
  invoiceSendLang.value = 'en'
  invoiceSendLangDialogVisible.value = true
}

const submitCustomerInvoiceSend = async () => {
  const row = pendingSendInvoiceRow.value
  if (!row?.id) return
  invoiceSending.value = true
  try {
    const res = await sendInvoice(row.id, invoiceSendLang.value)
    const payload = res?.data ?? res
    const sentEmail = payload?.email ?? payload?.data?.email ?? payload?.result?.email ?? ''
    if (sentEmail) {
      ElMessage.success(`${t('invoice.invoiceSentSuccess')} ${sentEmail}`)
    } else {
      ElMessage.success(t('invoice.sendSuccess'))
    }
    invoiceSendLangDialogVisible.value = false
    await loadCustomerIssuedInvoices()
  } catch (error) {
    const errorMessage = error?.response?.data?.detail || error?.message || t('invoice.sendFailed')
    ElMessage.error(errorMessage)
  } finally {
    invoiceSending.value = false
  }
}

const handleCustomerInvoiceDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `${t('invoice.deleteConfirm', { number: row.invoice_number })}\n删除后，该发票关联的任务将回退到“未开发票”。`,
      t('invoice.confirmDelete'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    await deleteInvoice(row.id)
    ElMessage.success(`${t('invoice.deleteSuccess')}（任务已回退到未开发票）`)
    await Promise.all([loadCustomerIssuedInvoices(), loadCustomerUnissuedTasks()])
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || t('invoice.deleteFailed'))
    }
  }
}

const getUnissuedServiceCodes = (row) => {
  const rawList = Array.isArray(row?.services) ? row.services : (Array.isArray(row?.service_items) ? row.service_items : [])
  const codes = rawList.map((s) => normalizeString(s?.service_code || s?.code || '')).filter(Boolean)
  if (!codes.length) {
    const fallback = normalizeString(row?.service_code || '')
    if (fallback) codes.push(fallback)
  }
  return Array.from(new Set(codes))
}

const getUnissuedTotalAmount = (row) => {
  const direct = row?.total_amount != null ? Number(row.total_amount) : null
  if (direct != null && !isNaN(direct)) return direct
  const list = Array.isArray(row?.services) ? row.services : (Array.isArray(row?.service_items) ? row.service_items : [])
  if (!list.length) return Number(row?.total_price || 0) || 0
  return list.reduce((sum, s) => {
    const p = Number(s?.total_price != null ? s.total_price : (Number(s?.unit_price || 0) * Number(s?.duration_hours || 0)))
    return sum + (isNaN(p) ? 0 : p)
  }, 0)
}

const loadCustomerUnissuedTasks = async () => {
  customerUnissuedLoading.value = true
  try {
    const res = await getTasksForInvoice({ customer_id: customerId })
    const list = getArrayFromResponse(res)
    customerUnissuedTasks.value = list.map((r) => ({ ...r, id: r?.id ?? r?.task_id ?? r?.taskId }))
  } catch {
    customerUnissuedTasks.value = []
  } finally {
    customerUnissuedLoading.value = false
  }
}

const customerUnissuedTotal = computed(() => (Array.isArray(customerUnissuedTasks.value) ? customerUnissuedTasks.value.length : 0))

const customerUnissuedPagedRows = computed(() => {
  const list = Array.isArray(customerUnissuedTasks.value) ? customerUnissuedTasks.value : []
  const page = Number(customerUnissuedPage.value) || 1
  const size = Number(customerUnissuedPageSize.value) || 10
  const start = (page - 1) * size
  return list.slice(start, start + size)
})

watch([customerUnissuedPageSize], () => {
  customerUnissuedPage.value = 1
})

const getUnissuedRowTaskId = (row) => row?.task_id || row?.taskId || row?.id || ''

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
  const customerPayload = payload?.customer || null
  const employeePayload = payload?.employee || payload?.assigned_employee || null
  const serviceLinesRaw = payload?.service_lines || payload?.serviceLines || payload?.services || payload?.service_items || []
  const serviceLines = Array.isArray(serviceLinesRaw) ? serviceLinesRaw : []
  const items = serviceLines.map((l, idx) => normalizeServiceLine(l, idx))
  const total = items.reduce((sum, it) => sum + Number(it.amount || 0), 0)
  return { task, customer: customerPayload, employee: employeePayload, items, total_amount: Number(total.toFixed(2)) }
}

const openUnissuedGenerate = async (task) => {
  const tid = getUnissuedRowTaskId(task)
  if (!tid) return
  unissuedCurrentTask.value = { ...task, id: tid }
  const cid = task.customer_id || task.customer?.id || customerId || ''
  const cname = task.customer?.name || task.customer_name || customer.value?.name || ''
  const eid = task.assigned_employee_id || task.assigned_employee?.id || ''
  const ename = task.assigned_employee?.name || task.employee?.name || task.assigned_employee_name || task.employee_name || ''
  unissuedPreview.value.customerId = cid
  unissuedPreview.value.customerName = cname || '-'
  unissuedPreview.value.employeeId = eid
  unissuedPreview.value.employeeName = ename || '-'
  unissuedPreview.value.invoiceDate = new Date().toISOString().split('T')[0]
  unissuedDialogVisible.value = true

  unissuedPreviewLoading.value = true
  try {
    const detail = await getInvoiceTaskDetail(tid)
    const normalized = normalizeInvoiceTaskDetail(detail)
    const finalCustomerName = normalized.customer?.name || unissuedPreview.value.customerName || '-'
    const finalEmployeeName = normalized.employee?.name || unissuedPreview.value.employeeName || '-'
    unissuedPreview.value.customerName = finalCustomerName
    unissuedPreview.value.employeeName = finalEmployeeName
    unissuedPreview.value.items = normalized.items.map((it) => ({
      ...it,
      description: it.description || task.title || task.id
    }))
    unissuedPreview.value.totalAmount = normalized.total_amount
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('invoice.generateFailed'))
    unissuedDialogVisible.value = false
  } finally {
    unissuedPreviewLoading.value = false
  }
}

const confirmUnissuedGenerate = async () => {
  if (!unissuedCurrentTask.value?.id) return
  try {
    unissuedGenerating.value = true
    const taskId = unissuedCurrentTask.value.id
    const fmtDate = (s) => {
      if (!s || typeof s !== 'string') return ''
      const parts = s.split(' ')
      return parts[0] || ''
    }
    const fmtHHmm = (s) => {
      if (!s || typeof s !== 'string') return ''
      if (s.length === 4 && /^\d{4}$/.test(s)) return s
      const tt = s.includes(' ') ? s.split(' ')[1] || '' : s
      const hh = tt.slice(0, 2)
      const mm = tt.slice(3, 5)
      return hh && mm ? `${hh}${mm}` : ''
    }
    const items = Array.isArray(unissuedPreview.value.items) ? unissuedPreview.value.items : []
    const payload = {
      customer_id: unissuedPreview.value.customerId || null,
      employee_id: unissuedPreview.value.employeeId || null,
      invoice_date: unissuedPreview.value.invoiceDate,
      items: items.map((it) => {
        const unit = it?.price != null ? Number(it.price) : (it?.unit_price != null ? Number(it.unit_price) : 0)
        const qty = it?.quantity != null ? Number(it.quantity) : (it?.duration_hours != null ? Number(it.duration_hours) : 0)
        const amt = it?.amount != null ? Number(it.amount) : Number((unit * qty).toFixed(2))
        return {
          task_service_item_id: it?.task_service_item_id || it?.id || null,
          description: it?.description || unissuedCurrentTask.value.title || unissuedCurrentTask.value.id || '',
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
    unissuedDialogVisible.value = false
    await Promise.all([loadCustomerUnissuedTasks(), loadCustomerIssuedInvoices()])
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
            const tt = s.includes(' ') ? s.split(' ')[1] || '' : s
            const hh = tt.slice(0, 2)
            const mm = tt.slice(3, 5)
            return hh && mm ? `${hh}${mm}` : ''
          }
          const price = Number(it?.price != null ? it.price : (it?.unit_price || 0))
          const qty = Number(it?.quantity != null ? it.quantity : (it?.duration_hours || 0))
          const amount = Number(it?.amount != null ? it.amount : Number((price * qty).toFixed(2)))
          return {
            task_id: taskId,
            description: it?.description || unissuedCurrentTask.value.title || unissuedCurrentTask.value.id || '',
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
          customer_id: unissuedPreview.value.customerId || null,
          invoice_date: `${unissuedPreview.value.invoiceDate}T00:00:00.000Z`,
          items: toItems
        })
      } catch {}
      router.push(`/invoices/${id}`)
    }
    unissuedCurrentTask.value = null
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('invoice.generateFailed'))
  } finally {
    unissuedGenerating.value = false
  }
}

const openEdit = async () => {
  if (!serviceLevelOptions.value.length) {
    await loadServiceLevels()
  }
  const c = customer.value || {}
  Object.assign(editForm, {
    name: c.name || '',
    phone: c.phone || '',
    email: c.email || '',
    address: c.address || '',
    customer_type: c.customer_type || '',
    weekly_service_hours: c.weekly_service_hours ?? null,
    gender: c.gender || '',
    age: c.age != null ? c.age : null,
    disability_type: c.disability_type || '',
    introduction: c.introduction || '',
    notes: c.notes || '',
    accepted_service_level1_ids: Array.isArray(c.accepted_service_level1_ids) ? c.accepted_service_level1_ids : [],
    emergency_contact1_name: c.emergency_contact1_name || '',
    emergency_contact1_phone: c.emergency_contact1_phone || '',
    emergency_contact1_email: c.emergency_contact1_email || '',
    emergency_contact2_name: c.emergency_contact2_name || '',
    emergency_contact2_phone: c.emergency_contact2_phone || '',
    emergency_contact2_email: c.emergency_contact2_email || ''
  })
  editDialogVisible.value = true
}

const submitEdit = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    editSaving.value = true
    try {
      await updateCustomer(customerId, {
        name: editForm.name,
        phone: editForm.phone,
        email: editForm.email || null,
        address: editForm.address,
        customer_type: editForm.customer_type || null,
        weekly_service_hours: editForm.weekly_service_hours,
        gender: editForm.gender || null,
        age: editForm.age,
        disability_type: editForm.disability_type || null,
        introduction: editForm.introduction || null,
        notes: editForm.notes || null,
        accepted_service_level1_ids: Array.isArray(editForm.accepted_service_level1_ids) ? editForm.accepted_service_level1_ids : [],
        emergency_contact1_name: editForm.emergency_contact1_name || null,
        emergency_contact1_phone: editForm.emergency_contact1_phone || null,
        emergency_contact1_email: editForm.emergency_contact1_email || null,
        emergency_contact2_name: editForm.emergency_contact2_name || null,
        emergency_contact2_phone: editForm.emergency_contact2_phone || null,
        emergency_contact2_email: editForm.emergency_contact2_email || null
      })
      ElMessage.success(t('customer.updateSuccess'))
      editDialogVisible.value = false
      await loadCustomer()
    } catch (e) {
      ElMessage.error(e?.response?.data?.detail || e?.message || t('customer.operationFailed'))
    } finally {
      editSaving.value = false
    }
  })
}

onMounted(() => {
  loadCustomer()
  loadEmployees()
  markUpdatesRead('customer', customerId).catch(() => {})
})

watch(
  () => activeTab.value,
  (tab) => {
    if (tab === 'tasks') {
      if (!customerTaskAllRows.value.length) loadCustomerTasks()
    }
    if (tab === 'invoices') {
      if (!customerIssuedInvoices.value.length) loadCustomerIssuedInvoices()
      if (!customerUnissuedTasks.value.length) loadCustomerUnissuedTasks()
    }
  }
)

const statusTagType = (s) => {
  if (s === '未建档') return 'info'
  if (s === '待建档') return 'warning'
  if (s === '已建档') return 'success'
  return ''
}

const formatEmergencyContact = (idx) => {
  const c = customer.value || {}
  const name = c[`emergency_contact${idx}_name`] || ''
  const phone = c[`emergency_contact${idx}_phone`] || ''
  const email = c[`emergency_contact${idx}_email`] || ''
  const parts = [name, phone, email].map((s) => String(s || '').trim()).filter(Boolean)
  return parts.length ? parts.join(' / ') : '-'
}
</script>

<style scoped>
.customer-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.status-tag {
  display: inline-flex;
  align-items: center;
  height: var(--el-component-size);
  padding: 0 14px;
  font-size: var(--el-font-size-base);
}

:deep(.el-descriptions) {
  --el-descriptions-item-label-font-size: var(--el-font-size-base);
  --el-descriptions-item-content-font-size: var(--el-font-size-base);
}

:deep(.el-descriptions__label),
:deep(.el-descriptions__content),
:deep(.el-descriptions__cell) {
  font-size: var(--el-font-size-base) !important;
}

:deep(.el-tabs__item) {
  font-size: var(--el-font-size-base);
}

.embedded-pane {
  padding-top: 12px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.pager-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.item-amount {
  font-weight: 600;
}

.action-buttons {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.action-buttons-inner {
  display: inline-flex;
  gap: 8px;
}

.edit-items-toolbar {
  margin-bottom: 10px;
}
</style>
