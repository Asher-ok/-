<template>
  <div class="invoice-list">
    <template v-if="isServiceEditor">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>{{ $t('invoice.editService') }}</span>
            <div class="service-toolbar">
              <el-button type="primary" @click="openServiceRuleDialog()">{{ $t('invoice.addServiceRule') }}</el-button>
              <el-switch v-model="serviceShowInactive" active-text="显示已删除" @change="reloadServiceAll" />
              <el-button @click="reloadServiceAll" :loading="serviceLoading.level1">{{ $t('common.refresh') }}</el-button>
            </div>
          </div>
        </template>

        <el-form class="service-filters" :label-position="isMobile ? 'top' : 'right'">
          <el-form-item :label="$t('task.serviceLevel1')">
            <el-select v-model="serviceFilter.level1_id" filterable clearable :style="{ width: isMobile ? '100%' : '220px' }" @change="handleServiceLevel1Change">
              <el-option v-for="opt in serviceLevel1Options" :key="opt.id" :label="opt.is_active === false ? opt.name + '（已删除）' : opt.name" :value="opt.id" />
            </el-select>
            <el-button size="small" plain @click="openServiceLevelDialog('level1', null)">{{ $t('common.add') }}</el-button>
            <el-button size="small" plain :disabled="!serviceFilter.level1_id" @click="openServiceLevelDialog('level1', serviceFilter.level1_id)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" plain type="danger" :disabled="!serviceFilter.level1_id" @click="handleDeleteServiceLevel('level1', serviceFilter.level1_id)">{{ $t('common.delete') }}</el-button>
          </el-form-item>

          <el-form-item :label="$t('task.serviceLevel2')">
            <el-select v-model="serviceFilter.level2_id" filterable clearable :style="{ width: isMobile ? '100%' : '220px' }" :disabled="!serviceFilter.level1_id" @change="handleServiceLevel2Change">
              <el-option v-for="opt in serviceLevel2Options" :key="opt.id" :label="opt.is_active === false ? opt.name + '（已删除）' : opt.name" :value="opt.id" />
            </el-select>
            <el-button size="small" plain :disabled="!serviceFilter.level1_id" @click="openServiceLevelDialog('level2', null)">{{ $t('common.add') }}</el-button>
            <el-button size="small" plain :disabled="!serviceFilter.level2_id" @click="openServiceLevelDialog('level2', serviceFilter.level2_id)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" plain type="danger" :disabled="!serviceFilter.level2_id" @click="handleDeleteServiceLevel('level2', serviceFilter.level2_id)">{{ $t('common.delete') }}</el-button>
          </el-form-item>

          <el-form-item :label="$t('task.serviceLevel3')">
            <el-select v-model="serviceFilter.level3_id" filterable clearable :style="{ width: isMobile ? '100%' : '220px' }" :disabled="!serviceFilter.level1_id" @change="handleServiceLevel3Change">
              <el-option v-for="opt in serviceLevel3Options" :key="opt.id" :label="opt.is_active === false ? opt.name + '（已删除）' : opt.name" :value="opt.id" />
            </el-select>
            <el-button size="small" plain :disabled="!serviceFilter.level1_id" @click="openServiceLevelDialog('level3', null)">{{ $t('common.add') }}</el-button>
            <el-button size="small" plain :disabled="!serviceFilter.level3_id" @click="openServiceLevelDialog('level3', serviceFilter.level3_id)">{{ $t('common.edit') }}</el-button>
            <el-button size="small" plain type="danger" :disabled="!serviceFilter.level3_id" @click="handleDeleteServiceLevel('level3', serviceFilter.level3_id)">{{ $t('common.delete') }}</el-button>
          </el-form-item>
        </el-form>

        <el-table :data="serviceCodeRows" v-loading="serviceLoading.codes" stripe>
          <el-table-column :label="$t('invoice.serviceCode')" min-width="160">
            <template #default="{ row }">
              <span>{{ row.code || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.description')" min-width="220">
            <template #default="{ row }">
              <span>{{ row.description || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.unitPrice')" width="140">
            <template #default="{ row }">
              <span>${{ formatAmountNumber(row.unit_price) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.operations')" width="220" :fixed="isMobile ? false : 'right'">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="openServiceRuleDialog(row)">{{ $t('common.edit') }}</el-button>
              <el-button size="small" type="danger" @click="handleDeleteServiceCode(row)">{{ $t('common.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <template v-else>
      <div v-if="viewMode === 'all'" class="task-embed">
        <TaskList />
      </div>
      <div v-else-if="viewMode === 'issued'">
        <el-card>
          <div class="card-header" style="padding-bottom: 12px;">
            <span>{{ pageTitle }}</span>
            <el-button type="primary" :loading="sendingAll" @click="handleBatchSendUnsent">
              <el-icon><Promotion /></el-icon>
              {{ $t('invoice.batchSendUnsent') }}
            </el-button>
          </div>
          <div class="filter-bar">
            <el-select
              v-model="issuedFilters.invoice_number"
              :placeholder="$t('invoice.invoiceNumber')"
              clearable
              filterable
              allow-create
              default-first-option
              :style="{ width: isMobile ? '100%' : '240px' }"
              @change="handleIssuedSearch"
            >
              <el-option v-for="opt in issuedInvoiceNumberOptions" :key="opt" :label="opt" :value="opt" />
            </el-select>
            <el-select
              v-model="issuedFilters.customer_id"
              :placeholder="$t('invoice.customer')"
              clearable
              filterable
              :style="{ width: isMobile ? '100%' : '240px' }"
              @change="handleIssuedSearch"
            >
              <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-button type="primary" @click="handleIssuedSearch">{{ $t('common.search') }}</el-button>
            <el-button @click="handleIssuedReset">{{ $t('task.reset') }}</el-button>
          </div>
          <el-table
            :data="pagedInvoices"
            v-loading="loading"
            stripe
            table-layout="auto"
            style="width: 100%"
            :default-sort="{ prop: 'invoice_date', order: 'descending' }"
            @sort-change="handleIssuedSortChange"
          >
            <el-table-column prop="invoice_number" :label="$t('invoice.invoiceNumber')" min-width="240">
              <template #default="{ row }">
                <el-link type="primary" class="clickable-text" :underline="true" @click="handleView(row)">{{ row.invoice_number || '-' }}</el-link>
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.customer')" min-width="220">
              <template #default="{ row }">
                {{ row.customer?.name || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="invoice_date" column-key="invoice_date" :label="$t('invoice.invoiceDate')" min-width="200" sortable="custom">
              <template #default="{ row }">
                {{ formatDate(row.invoice_date, 'YYYY-MM-DD') }}
              </template>
            </el-table-column>
            <el-table-column prop="service_start_time" column-key="service_start_time" :label="$t('task.serviceStartTime')" min-width="200" sortable="custom">
              <template #default="{ row }">
                {{ formatDateTimeToMinute(getInvoiceServiceStartTime(row)) }}
              </template>
            </el-table-column>
            <el-table-column prop="service_end_time" column-key="service_end_time" :label="$t('task.serviceEndTime')" min-width="200" sortable="custom">
              <template #default="{ row }">
                {{ formatDateTimeToMinute(getInvoiceServiceEndTime(row)) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_amount" :label="$t('invoice.totalAmount')" min-width="200">
              <template #default="{ row }">
                ${{ row.total_amount }}
              </template>
            </el-table-column>
            <el-table-column prop="status" :label="$t('invoice.status')" min-width="160">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.operations')" width="240" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
              <template #default="{ row }">
                <div class="action-buttons action-buttons--scroll">
                  <div class="action-buttons-inner">
                    <el-button type="success" size="small" @click="handleEdit(row)">{{ $t('invoice.edit') }}</el-button>
                    <el-button v-if="row.pdf_url && (row.status === 'draft' || row.status === 'sent' || row.status === 'paid')" type="warning" size="small" @click="handleSend(row)">
                      {{ $t('invoice.send') }}
                    </el-button>
                    <el-button type="danger" size="small" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
                  </div>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager-bar">
            <el-pagination
              v-model:current-page="issuedPage"
              v-model:page-size="issuedPageSize"
              :page-sizes="[10]"
              layout="total, prev, pager, next"
              :total="issuedTotal"
            />
          </div>
        </el-card>
      </div>
      <div v-else>
        <el-card>
          <div class="card-header" style="padding-bottom: 12px;">
            <span>{{ pageTitle }}</span>
            <el-button type="primary" @click="showBatchGenerateDialog = true">
              <el-icon><Plus /></el-icon>
              {{ $t('invoice.batchGenerate') }}
            </el-button>
          </div>
          <div class="filter-bar">
            <el-select
              v-model="unissuedFilters.task_title"
              :placeholder="$t('task.title')"
              clearable
              filterable
              allow-create
              default-first-option
              :style="{ width: isMobile ? '100%' : '240px' }"
              @change="handleUnissuedSearch"
            >
              <el-option v-for="opt in unissuedTaskTitleOptions" :key="opt" :label="opt" :value="opt" />
            </el-select>
            <el-select
              v-model="unissuedFilters.customer_id"
              :placeholder="$t('invoice.customer')"
              clearable
              filterable
              :style="{ width: isMobile ? '100%' : '240px' }"
              @change="handleUnissuedSearch"
            >
              <el-option v-for="c in customers" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-select
              v-model="unissuedFilters.employee_id"
              :placeholder="$t('task.assignedEmployeeLabel')"
              clearable
              filterable
              :style="{ width: isMobile ? '100%' : '240px' }"
              @change="handleUnissuedSearch"
            >
              <el-option v-for="e in employees" :key="e.id" :label="`${e.name}（${e.employee_number}）`" :value="e.id" />
            </el-select>
            <el-button type="primary" @click="handleUnissuedSearch">{{ $t('common.search') }}</el-button>
            <el-button @click="handleUnissuedReset">{{ $t('task.reset') }}</el-button>
          </div>
          <el-table
            :data="pagedUnissuedTasks"
            v-loading="loadingUnissued"
            stripe
            :default-sort="{ prop: 'service_end_time', order: 'descending' }"
            @sort-change="handleUnissuedSortChange"
          >
            <el-table-column prop="title" :label="$t('task.title')" min-width="180" />
            <el-table-column :label="$t('invoice.customer')" min-width="140">
              <template #default="{ row }">
                <span>{{ row.customer?.name || row.customer_name || '-' }}</span>
              </template>
            </el-table-column>
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
            <el-table-column prop="service_start_time" column-key="service_start_time" :label="$t('task.serviceStartTime')" min-width="200" sortable="custom">
              <template #default="{ row }">
                <span>{{ formatDateTimeToMinute(row.service_start_time) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="service_end_time" column-key="service_end_time" :label="$t('task.serviceEndTime')" min-width="200" sortable="custom">
              <template #default="{ row }">
                <span>{{ formatDateTimeToMinute(row.service_end_time) }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.totalAmount')" width="140">
              <template #default="{ row }">
                <span>${{ formatAmountNumber(getUnissuedTotalAmount(row)) }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.operations')" width="180" :fixed="isMobile ? false : 'right'">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="openGenerateForTask(row)">{{ $t('invoice.generateInvoice') }}</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager-bar">
            <el-pagination
              v-model:current-page="unissuedPage"
              v-model:page-size="unissuedPageSize"
              :page-sizes="[10]"
              layout="total, prev, pager, next"
              :total="unissuedTotal"
            />
          </div>
        </el-card>
      </div>
    </template>

    <el-dialog v-model="showUnissuedGenerateDialog" :title="$t('invoice.generateInvoice')" width="900px" :close-on-click-modal="false">
      <div v-loading="unissuedPreviewLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('task.title')">{{ unissuedPreview.task?.title || unissuedPreview.task?.id || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('invoice.totalAmount')">${{ formatAmountNumber(unissuedPreview.total_amount) }}</el-descriptions-item>
          <el-descriptions-item :label="$t('invoice.customer')">{{ unissuedPreview.customer?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('task.assignedEmployeeLabel')">{{ unissuedPreview.employee?.name || '-' }}</el-descriptions-item>
        </el-descriptions>

        <el-form label-width="120px" style="margin-top: 12px">
          <el-form-item label="客户已付款">
            <el-switch v-model="unissuedIsPaid" />
          </el-form-item>
        </el-form>

        <el-divider>{{ $t('invoice.invoiceItems') }}</el-divider>
        <el-table :data="unissuedPreview.service_lines || []" stripe>
          <el-table-column :label="$t('invoice.description')" min-width="200">
            <template #default="{ row }">
              <span>{{ row.description || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceCode')" width="160">
            <template #default="{ row }">
              <span>{{ row.code || row.service_code || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.unitPrice')" width="120">
            <template #default="{ row }">
              <span>${{ formatAmountNumber(row.unit_price) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.serviceDuration')" width="120">
            <template #default="{ row }">
              <span>{{ row.quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.amount')" width="120">
            <template #default="{ row }">
              <span class="item-amount">${{ formatAmountNumber(row.amount) }}</span>
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
        <el-button @click="showUnissuedGenerateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="unissuedGenerating" @click="confirmUnissuedGenerate">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showBatchGenerateDialog" :title="$t('invoice.batchGenerateTitle')" width="900px" :close-on-click-modal="false">
      <div v-loading="batchPreviewLoading">
        <component :is="'style'">{{ uninvoicedBadgeCssText }}</component>
        <el-form inline>
          <el-form-item label="时间范围">
            <el-radio-group v-model="batchRangePreset">
              <el-radio-button label="week">一周</el-radio-button>
              <el-radio-button label="month">一月</el-radio-button>
              <el-radio-button label="custom">自定义</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item>
            <el-date-picker
              v-model="batchDateRange"
              type="daterange"
              :range-separator="$t('common.to')"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              style="width: 320px"
              value-format="YYYY-MM-DD"
              :disabled="batchRangePreset !== 'custom'"
              popper-class="uninvoiced-date-range-popper"
              :cell-class-name="getUninvoicedCellClassName"
            />
          </el-form-item>
          <el-form-item>
            <el-button @click="loadBatchPreview" :loading="batchPreviewLoading">{{ $t('common.refresh') }}</el-button>
          </el-form-item>
        </el-form>
        <div style="margin: 8px 0 12px; color: var(--el-text-color-secondary);">
          按客户合并生成：同一客户的多个任务会生成一张发票
        </div>
        <el-table :data="batchPreviewTasks" stripe>
          <el-table-column type="expand">
            <template #default="{ row }">
              <el-table :data="Array.isArray(row.service_lines) ? row.service_lines : []" size="small" stripe>
                <el-table-column :label="$t('invoice.description')" min-width="200">
                  <template #default="{ row: line }">
                    <span>{{ line.description || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('invoice.serviceCode')" width="150">
                  <template #default="{ row: line }">
                    <span>{{ line.code || line.service_code || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('invoice.unitPrice')" width="120">
                  <template #default="{ row: line }">
                    <span>${{ formatAmountNumber(line.unit_price) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('invoice.serviceDuration')" width="120">
                  <template #default="{ row: line }">
                    <span>{{ line.quantity }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('invoice.amount')" width="120">
                  <template #default="{ row: line }">
                    <span class="item-amount">${{ formatAmountNumber(line.amount) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('task.serviceStartTime')" width="170">
                  <template #default="{ row: line }">
                    <span>{{ formatDateTimeToMinute(line.service_time_start) }}</span>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('task.serviceEndTime')" width="170">
                  <template #default="{ row: line }">
                    <span>{{ formatDateTimeToMinute(line.service_time_end) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </template>
          </el-table-column>
          <el-table-column :label="$t('task.title')" min-width="180">
            <template #default="{ row }">
              <span>{{ row.title || row.task_id }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.customer')" min-width="160">
            <template #default="{ row }">
              <span>{{ row.customer?.name || row.customer_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('task.assignedEmployeeLabel')" min-width="160">
            <template #default="{ row }">
              <span>{{ row.employee?.name || row.employee_name || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('task.serviceStartTime')" width="170">
            <template #default="{ row }">
              <span>{{ formatDateTimeToMinute(getBatchTaskStartTime(row)) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('task.serviceEndTime')" width="170">
            <template #default="{ row }">
              <span>{{ formatDateTimeToMinute(getBatchTaskEndTime(row)) }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('invoice.totalAmount')" width="140">
            <template #default="{ row }">
              <span class="item-amount">${{ formatAmountNumber(row.subtotal || row.total_amount || 0) }}</span>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!batchPreviewLoading && batchPreviewTasks.length === 0" :description="$t('common.noData')" />
      </div>
      <template #footer>
        <el-button @click="showBatchGenerateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="batchGenerating" @click="confirmBatchGenerate">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showEditDialog" :title="$t('invoice.editInvoice')" width="900px" :close-on-click-modal="false">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="120px" v-loading="editLoading">
        <el-form-item :label="$t('invoice.invoiceNumber')">
          <el-input v-model="editForm.invoice_number" disabled />
        </el-form-item>
        <el-form-item :label="$t('invoice.customer')" prop="customer_id">
          <el-select v-model="editForm.customer_id" :placeholder="$t('invoice.selectCustomer')" style="width: 100%">
            <el-option v-for="customer in customers" :key="customer.id" :label="customer.name" :value="customer.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('invoice.invoiceDate')" prop="invoice_date">
          <el-date-picker v-model="editForm.invoice_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>

        <el-divider>{{ $t('invoice.invoiceItems') }}</el-divider>
        <div class="edit-items-toolbar">
          <el-button type="primary" plain size="small" @click="handleAddEditItem">{{ $t('invoice.addItem') }}</el-button>
        </div>
        <el-table :data="editForm.items" stripe>
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
              <span class="item-amount">${{ formatAmount(row) }}</span>
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
              <el-button type="danger" size="small" @click="handleRemoveEditItem($index)">{{ $t('invoice.removeItem') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleUpdate">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="showGenerateDialog" :title="$t('invoice.generateInvoice')" width="760px">
      <el-form :model="generateForm" :rules="generateRules" ref="generateFormRef" label-width="auto">
        <el-form-item :label="$t('invoice.customer')" prop="customer_id">
          <el-select v-model="generateForm.customer_id" :placeholder="$t('invoice.selectCustomer')" style="width: 100%">
            <el-option v-for="customer in customers" :key="customer.id" :label="customer.name" :value="customer.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('invoice.selectEmployee')" prop="employee_id">
          <el-select v-model="generateForm.employee_id" :placeholder="$t('invoice.selectEmployee')" style="width: 100%">
            <el-option v-for="employee in employees" :key="employee.id" :label="`${employee.name} (${employee.employee_number})`" :value="employee.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('invoice.dateRange')" prop="date_range">
          <el-date-picker
            v-model="generateForm.date_range"
            type="daterange"
            :range-separator="$t('common.to')"
            :start-placeholder="$t('invoice.startDate')"
            :end-placeholder="$t('invoice.endDate')"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item :label="$t('invoice.project')" prop="task_ids">
          <el-select v-model="generateForm.task_ids" :placeholder="$t('invoice.selectTask')" style="width: 100%" :loading="loadingTasks" filterable multiple collapse-tags collapse-tags-tooltip>
            <el-option 
              v-for="task in tasks" 
              :key="task.id" 
              :label="task.title || task.id" 
              :value="task.id" 
            >
              <span class="task-option-title">{{ task.title || task.id }}</span>
              <span class="task-option-id">{{ task.id }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('invoice.invoiceItems')" required>
          <el-table :data="selectedTaskItems" stripe>
            <el-table-column :label="$t('invoice.description')" min-width="180">
              <template #default="{ row }">
                <span>{{ row.title || row.task_id }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.serviceCode')" width="160">
              <template #default="{ row }">
                <span>{{ row.service_code || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.unitPrice')" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.price" :min="0.01" :precision="2" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.serviceDuration')" width="140">
              <template #default="{ row }">
                <el-input-number v-model="row.quantity" :min="0.01" :precision="2" controls-position="right" />
              </template>
            </el-table-column>
            <el-table-column :label="$t('invoice.totalPrice')" width="140">
              <template #default="{ row }">
                <span class="item-amount">${{ formatAmount(row) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="selectedTaskItems.length === 0" :description="$t('invoice.selectTask')" />
        </el-form-item>
        <el-form-item :label="$t('invoice.invoiceDate')" prop="invoice_date">
          <el-date-picker v-model="generateForm.invoice_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="客户已付款">
          <el-switch v-model="generateForm.is_paid" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGenerateDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleGenerate">{{ $t('invoice.generate') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="serviceLevelDialogVisible" :title="serviceLevelDialogTitle" width="620px" :close-on-click-modal="false">
      <el-form :model="serviceLevelDialogForm" ref="serviceLevelDialogFormRef" label-width="auto" v-loading="serviceLevelDialogSaving">
        <el-form-item v-if="serviceLevelDialogType !== 'level1'" label="一级">
          <el-input :model-value="currentServiceLevel1?.name || '-'" disabled />
        </el-form-item>
        <el-form-item v-if="serviceLevelDialogType === 'level3'" label="二级">
          <el-input :model-value="currentServiceLevel2?.name || '（无）'" disabled />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="serviceLevelDialogForm.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serviceLevelDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveServiceLevel">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="serviceRuleDialogVisible" :title="serviceRuleDialogTitle" width="880px" :close-on-click-modal="false">
      <el-form :model="serviceRuleForm" ref="serviceRuleFormRef" label-width="auto" v-loading="serviceRuleDialogSaving">
        <el-form-item label="一级">
          <el-radio-group v-model="serviceRuleForm.level1_mode">
            <el-radio label="select">选择已有</el-radio>
            <el-radio label="new">新建一级</el-radio>
          </el-radio-group>
          <div v-if="serviceRuleForm.level1_mode === 'select'" style="margin-top: 8px">
            <el-select v-model="serviceRuleForm.level1_id" filterable style="width: 100%" @change="handleRuleLevel1Change">
              <el-option v-for="opt in serviceLevel1Options" :key="opt.id" :label="opt.name" :value="opt.id" />
            </el-select>
          </div>
          <div v-else style="margin-top: 8px">
            <el-input v-model="serviceRuleForm.level1_name" placeholder="请输入一级名称" />
          </div>
        </el-form-item>

        <el-form-item label="二级（可选）">
          <el-radio-group v-model="serviceRuleForm.level2_mode">
            <el-radio label="none">无二级</el-radio>
            <el-radio label="select">选择已有</el-radio>
            <el-radio label="new">新建二级</el-radio>
          </el-radio-group>
          <div v-if="serviceRuleForm.level2_mode === 'select'" style="margin-top: 8px">
            <el-select v-model="serviceRuleForm.level2_id" filterable style="width: 100%" :disabled="serviceRuleForm.level1_mode !== 'select' || !serviceRuleForm.level1_id" @change="handleRuleLevel2Change">
              <el-option v-for="opt in ruleLevel2Options" :key="opt.id" :label="opt.name" :value="opt.id" />
            </el-select>
          </div>
          <div v-else-if="serviceRuleForm.level2_mode === 'new'" style="margin-top: 8px">
            <el-input v-model="serviceRuleForm.level2_name" placeholder="请输入二级名称" :disabled="serviceRuleForm.level1_mode === 'select' && !serviceRuleForm.level1_id" />
          </div>
        </el-form-item>

        <el-form-item label="三级">
          <el-radio-group v-model="serviceRuleForm.level3_mode">
            <el-radio label="select">选择已有</el-radio>
            <el-radio label="new">新建三级</el-radio>
          </el-radio-group>
          <div v-if="serviceRuleForm.level3_mode === 'select'" style="margin-top: 8px">
            <el-select v-model="serviceRuleForm.level3_id" filterable style="width: 100%" :disabled="serviceRuleForm.level1_mode !== 'select' || !serviceRuleForm.level1_id" @change="handleRuleLevel3Change">
              <el-option v-for="opt in ruleLevel3Options" :key="opt.id" :label="opt.name" :value="opt.id" />
            </el-select>
          </div>
          <div v-else style="margin-top: 8px">
            <el-input v-model="serviceRuleForm.level3_name" placeholder="请输入三级名称" :disabled="serviceRuleForm.level1_mode === 'select' && !serviceRuleForm.level1_id" />
          </div>
        </el-form-item>

        <el-form-item label="服务编码">
          <el-input v-model="serviceRuleForm.code" placeholder="如 04_104_0125_6_1" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="serviceRuleForm.description" />
        </el-form-item>
        <el-form-item label="单价">
          <el-input-number v-model="serviceRuleForm.unit_price" :min="0.01" :precision="2" controls-position="right" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="serviceRuleDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveServiceRule">{{ $t('common.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="sendLangDialogVisible" :title="$t('invoice.send')" width="360px">
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
        <el-button type="primary" :loading="sendLangSubmitting" @click="submitSendWithLang">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({
  name: 'Invoices'
})
import { ref, reactive, onMounted, watch, computed, inject, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import TaskList from '@/views/tasks/TaskList.vue'
import {
  getInvoices,
  getInvoice,
  generateInvoice,
  updateInvoice,
  sendInvoice,
  getTasksForInvoice,
  getInvoiceTaskDetail,
  generateInvoiceForTask,
  deleteInvoice,
  getServiceLevel1,
  getServiceLevel2,
  getServiceLevel3,
  getServiceCodes,
  createServiceLevel1,
  updateServiceLevel1,
  deleteServiceLevel1,
  createServiceLevel2,
  updateServiceLevel2,
  deleteServiceLevel2,
  createServiceLevel3,
  updateServiceLevel3,
  deleteServiceLevel3,
  createServiceCode,
  updateServiceCode,
  deleteServiceCode,
  batchSendUnsentInvoices,
  batchGenerateUninvoiced,
  getUninvoicedTasksDetail
} from '@/api/invoices'
import { getTask } from '@/api/tasks'
import { getCustomers } from '@/api/customers'
import { getEmployees } from '@/api/employees'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate, formatDateTimeToMinute } from '@/utils/formatters'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const isMobile = inject('isMobile', ref(false))

const router = useRouter()
const route = useRoute()
const isServiceEditor = computed(() => route.name === 'InvoiceServices' || route.path === '/invoice-services')
const viewMode = computed(() => {
  if (isServiceEditor.value) return 'services'
  if (route.meta?.invoiceTab) return route.meta.invoiceTab
  if (route.path.endsWith('/issued')) return 'issued'
  if (route.path.endsWith('/unissued')) return 'unissued'
  return 'all'
})
const pageTitle = computed(() => {
  const base = t('menu.tasks')
  if (viewMode.value === 'issued') return `${base}/${t('invoice.issuedTab')}`
  if (viewMode.value === 'unissued') return `${base}/${t('invoice.unissuedTab')}`
  return base
})
const invoices = ref([])
const issuedPage = ref(1)
const issuedPageSize = ref(10)
const customers = ref([])
const employees = ref([])
const tasks = ref([])
const selectedTaskItems = ref([])
const loading = ref(false)
const loadingTasks = ref(false)
const unissuedTasks = ref([])
const unissuedPage = ref(1)
const unissuedPageSize = ref(10)
const loadingUnissued = ref(false)

const issuedFilters = reactive({
  invoice_number: '',
  customer_id: ''
})
const unissuedFilters = reactive({
  task_title: '',
  customer_id: '',
  employee_id: ''
})
const issuedSortState = reactive({
  prop: 'invoice_date',
  order: 'descending'
})
const unissuedSortState = reactive({
  prop: 'service_end_time',
  order: 'descending'
})

const uniqueNonEmpty = (arr) => {
  const set = new Set()
  for (const v of arr) {
    const s = normalizeString(v)
    if (s) set.add(s)
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b))
}

const issuedInvoiceNumberOptions = computed(() => uniqueNonEmpty((invoices.value || []).map((r) => r?.invoice_number)))
const unissuedTaskTitleOptions = computed(() => uniqueNonEmpty((unissuedTasks.value || []).map((r) => r?.title)))
const toTime = (value) => {
  const ms = new Date(value || '').getTime()
  return Number.isFinite(ms) ? ms : 0
}

const normalizeIsoDatePart = (value) => {
  const s = value == null ? '' : String(value).trim()
  if (!s) return ''
  const m = s.match(/^(\d{4}-\d{2}-\d{2})/)
  return m ? m[1] : ''
}

const normalizeTimePart = (value) => {
  const s = value == null ? '' : String(value).trim()
  if (!s) return ''
  if (/^\d{4}$/.test(s)) return `${s.slice(0, 2)}:${s.slice(2, 4)}`
  const m = s.match(/^(\d{2}):(\d{2})/)
  return m ? `${m[1]}:${m[2]}` : ''
}

const buildIsoDateTime = (datePart, timePart) => {
  const d = normalizeIsoDatePart(datePart)
  if (!d) return ''
  const t = normalizeTimePart(timePart) || '00:00'
  return `${d}T${t}:00`
}

const getInvoiceServiceStartTime = (row) => {
  const items = Array.isArray(row?.items) ? row.items : []
  const fallbackDate = normalizeIsoDatePart(row?.invoice_date || row?.created_at || '')
  let min = ''
  let minMs = Infinity
  for (const it of items) {
    const datePart = normalizeIsoDatePart(it?.service_date) || fallbackDate
    const iso = buildIsoDateTime(datePart, it?.service_time_start)
    const ms = toTime(iso)
    if (ms > 0 && ms < minMs) {
      minMs = ms
      min = iso
    }
  }
  return min
}

const getInvoiceServiceEndTime = (row) => {
  const items = Array.isArray(row?.items) ? row.items : []
  const fallbackDate = normalizeIsoDatePart(row?.invoice_date || row?.created_at || '')
  let max = ''
  let maxMs = 0
  for (const it of items) {
    const datePart = normalizeIsoDatePart(it?.service_date) || fallbackDate
    const iso = buildIsoDateTime(datePart, it?.service_time_end)
    const ms = toTime(iso)
    if (ms > maxMs) {
      maxMs = ms
      max = iso
    }
  }
  return max
}

const filteredInvoices = computed(() => {
  const list = Array.isArray(invoices.value) ? invoices.value : []
  const inv = normalizeString(issuedFilters.invoice_number)
  const customerId = normalizeString(issuedFilters.customer_id)
  if (!inv && !customerId) return list
  return list.filter((row) => {
    if (inv && !includesText(row?.invoice_number, inv)) return false
    if (customerId) {
      const rowCustomerId = normalizeString(row?.customer_id || row?.customer?.id)
      if (rowCustomerId !== customerId) return false
    }
    return true
  })
})

const sortedInvoices = computed(() => {
  const list = [...filteredInvoices.value]
  const { prop, order } = issuedSortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'invoice_date') {
    return list.sort((a, b) => (toTime(a?.invoice_date || a?.created_at) - toTime(b?.invoice_date || b?.created_at)) * dir)
  }
  if (prop === 'service_start_time') {
    return list.sort((a, b) => (toTime(getInvoiceServiceStartTime(a)) - toTime(getInvoiceServiceStartTime(b))) * dir)
  }
  if (prop === 'service_end_time') {
    return list.sort((a, b) => (toTime(getInvoiceServiceEndTime(a)) - toTime(getInvoiceServiceEndTime(b))) * dir)
  }
  return list
})

const issuedTotal = computed(() => sortedInvoices.value.length)
const pagedInvoices = computed(() => {
  const list = sortedInvoices.value
  const page = Number(issuedPage.value) || 1
  const size = Number(issuedPageSize.value) || 10
  const start = (page - 1) * size
  return list.slice(start, start + size)
})

const filteredUnissuedTasks = computed(() => {
  const list = Array.isArray(unissuedTasks.value) ? unissuedTasks.value : []
  const title = normalizeString(unissuedFilters.task_title)
  const customerId = normalizeString(unissuedFilters.customer_id)
  const employeeId = normalizeString(unissuedFilters.employee_id)
  if (!title && !customerId && !employeeId) return list
  return list.filter((row) => {
    if (title && !includesText(row?.title, title)) return false
    if (customerId) {
      const rowCustomerId = normalizeString(row?.customer?.id || row?.customer_id || row?.customerId)
      if (rowCustomerId !== customerId) return false
    }
    if (employeeId) {
      const rowEmployeeId = normalizeString(
        row?.assigned_employee?.id ||
          row?.employee?.id ||
          row?.assigned_employee_id ||
          row?.employee_id ||
          row?.assigned_employeeId
      )
      if (rowEmployeeId !== employeeId) return false
    }
    return true
  })
})

const getUnissuedSortTime = (row) => row?.service_end_time || row?.service_start_time || row?.service_time || ''

const sortedUnissuedTasks = computed(() => {
  const list = [...filteredUnissuedTasks.value]
  const { prop, order } = unissuedSortState
  if (!prop || !order) return list
  const dir = order === 'ascending' ? 1 : -1
  if (prop === 'service_time') {
    return list.sort((a, b) => (toTime(getUnissuedSortTime(a)) - toTime(getUnissuedSortTime(b))) * dir)
  }
  if (prop === 'service_start_time') {
    return list.sort((a, b) => (toTime(a?.service_start_time) - toTime(b?.service_start_time)) * dir)
  }
  if (prop === 'service_end_time') {
    return list.sort((a, b) => (toTime(a?.service_end_time) - toTime(b?.service_end_time)) * dir)
  }
  return list
})

const unissuedTotal = computed(() => sortedUnissuedTasks.value.length)
const pagedUnissuedTasks = computed(() => {
  const list = sortedUnissuedTasks.value
  const page = Number(unissuedPage.value) || 1
  const size = Number(unissuedPageSize.value) || 10
  const start = (page - 1) * size
  return list.slice(start, start + size)
})

watch(invoices, () => {
  issuedPage.value = 1
})

watch(unissuedTasks, () => {
  unissuedPage.value = 1
})

watch(
  () => [issuedFilters.invoice_number, issuedFilters.customer_id],
  () => {
    issuedPage.value = 1
  }
)

watch(
  () => [unissuedFilters.task_title, unissuedFilters.customer_id, unissuedFilters.employee_id],
  () => {
    unissuedPage.value = 1
  }
)
const sendingAll = ref(false)
const sendLangDialogVisible = ref(false)
const sendLang = ref('en')
const sendLangSubmitting = ref(false)
const pendingSendType = ref('single')
const pendingSendInvoiceRow = ref(null)
const showUnissuedGenerateDialog = ref(false)
const unissuedPreviewLoading = ref(false)
const unissuedGenerating = ref(false)
const unissuedTaskId = ref('')
const unissuedIsPaid = ref(false)
const unissuedPreview = ref({
  task: null,
  customer: null,
  employee: null,
  service_lines: [],
  total_amount: 0
})
const showGenerateDialog = ref(false)
const generateFormRef = ref(null)
const showEditDialog = ref(false)
const editLoading = ref(false)
const editFormRef = ref(null)
const showBatchGenerateDialog = ref(false)
const batchPreviewLoading = ref(false)
const batchPreviewTasks = ref([])
const batchGenerating = ref(false)
const batchRangePreset = ref('week')
const batchDateRange = ref(null)

const normalizeString = (v) => (v == null ? '' : String(v)).trim()
const includesText = (source, keyword) => {
  const s = normalizeString(source).toLowerCase()
  const k = normalizeString(keyword).toLowerCase()
  if (!k) return true
  return s.includes(k)
}

const handleIssuedSearch = () => {
  issuedPage.value = 1
}

const handleIssuedSortChange = ({ prop, order }) => {
  issuedSortState.prop = prop || ''
  issuedSortState.order = order
  issuedPage.value = 1
}

const handleIssuedReset = () => {
  issuedFilters.invoice_number = ''
  issuedFilters.customer_id = ''
  issuedPage.value = 1
}

const handleUnissuedSearch = () => {
  unissuedPage.value = 1
}

const handleUnissuedSortChange = ({ prop, order }) => {
  unissuedSortState.prop = prop || ''
  unissuedSortState.order = order
  unissuedPage.value = 1
}

const handleUnissuedReset = () => {
  unissuedFilters.task_title = ''
  unissuedFilters.customer_id = ''
  unissuedFilters.employee_id = ''
  unissuedPage.value = 1
}

const extractDateKey = (value) => {
  const s = normalizeString(value)
  if (!s) return ''
  const m = s.match(/\d{4}-\d{2}-\d{2}/)
  if (m) return m[0]
  const m2 = s.match(/(\d{4})[/-](\d{1,2})[/-](\d{1,2})/)
  if (m2) {
    const y = m2[1]
    const mo = String(m2[2]).padStart(2, '0')
    const d = String(m2[3]).padStart(2, '0')
    return `${y}-${mo}-${d}`
  }
  const cn = s.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/)
  if (cn) {
    const y = cn[1]
    const mo = String(cn[2]).padStart(2, '0')
    const d = String(cn[3]).padStart(2, '0')
    return `${y}-${mo}-${d}`
  }
  const ts13 = s.match(/\b\d{13}\b/)
  if (ts13) return formatLocalDate(new Date(Number(ts13[0])))
  const ts10 = s.match(/\b\d{10}\b/)
  if (ts10) return formatLocalDate(new Date(Number(ts10[0]) * 1000))
  return ''
}

const toLocalDayKey = (value) => {
  if (!value) return ''
  if (typeof value === 'string') {
    const s = normalizeString(value)
    if (!s) return ''
    const only = extractDateKey(s)
    if (only && only.length === 10 && (s.length === 10 || /^\d{4}[-/]\d{1,2}[-/]\d{1,2}$/.test(s))) {
      return only
    }
    const normalized = s.includes('T') ? s : s.replace(' ', 'T')
    const d = new Date(normalized)
    if (!Number.isNaN(d.getTime())) return formatLocalDate(d)
    return only
  }
  const d = new Date(value)
  if (!Number.isNaN(d.getTime())) return formatLocalDate(d)
  return ''
}

const getBatchTaskStartTime = (row) => {
  if (row?.service_start_time) return row.service_start_time
  const lines = Array.isArray(row?.service_lines) ? row.service_lines : []
  for (const line of lines) {
    if (line?.service_time_start) return line.service_time_start
  }
  return ''
}

const getBatchTaskEndTime = (row) => {
  if (row?.service_end_time) return row.service_end_time
  const lines = Array.isArray(row?.service_lines) ? row.service_lines : []
  for (const line of lines) {
    if (line?.service_time_end) return line.service_time_end
  }
  return ''
}

const uninvoicedCountByDate = computed(() => {
  const map = {}
  const list = Array.isArray(unissuedTasks.value) ? unissuedTasks.value : []
  for (const row of list) {
    const day =
      toLocalDayKey(row?.service_end_time) ||
      toLocalDayKey(row?.service_time) ||
      toLocalDayKey(row?.service_start_time) ||
      ''
    if (!day) continue
    map[day] = (map[day] || 0) + 1
  }
  return map
})

const formatLocalDate = (d) => {
  if (!(d instanceof Date)) return ''
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const getUninvoicedCountLabel = (date) => {
  if (!(date instanceof Date)) return ''
  const key = formatLocalDate(date)
  const count = Number(uninvoicedCountByDate.value?.[key] || 0)
  if (!count || count <= 0) return ''
  return count > 99 ? '99+' : String(count)
}

const getUninvoicedCellClassName = (data) => {
  const date = data?.date instanceof Date ? data.date : data
  if (!(date instanceof Date)) return ''
  const key = formatLocalDate(date)
  const count = Number(uninvoicedCountByDate.value?.[key] || 0)
  if (!count || count <= 0) return ''
  return `uninvoiced-day-${key}`
}

const uninvoicedBadgeCssText = computed(() => {
  const map = uninvoicedCountByDate.value || {}
  const keys = Object.keys(map)
  if (!keys.length) return ''
  const rules = []
  for (const key of keys) {
    const count = Number(map[key] || 0)
    if (!count || count <= 0) continue
    const label = count > 99 ? '99+' : String(count)
    const content = JSON.stringify(label)
    const baseTd = `.uninvoiced-date-range-popper td.uninvoiced-day-${key}`
    const baseCell = `.uninvoiced-date-range-popper .el-date-table-cell.uninvoiced-day-${key}`
    const disabledTd = `.uninvoiced-date-range-popper td.disabled.uninvoiced-day-${key},.uninvoiced-date-range-popper td.is-disabled.uninvoiced-day-${key},.uninvoiced-date-range-popper td.prev-month.uninvoiced-day-${key},.uninvoiced-date-range-popper td.next-month.uninvoiced-day-${key}`
    const disabledCell = `.uninvoiced-date-range-popper td.disabled .el-date-table-cell.uninvoiced-day-${key},.uninvoiced-date-range-popper td.is-disabled .el-date-table-cell.uninvoiced-day-${key},.uninvoiced-date-range-popper td.prev-month .el-date-table-cell.uninvoiced-day-${key},.uninvoiced-date-range-popper td.next-month .el-date-table-cell.uninvoiced-day-${key}`
    rules.push(
      `${baseTd} .el-date-table-cell,${baseCell}{position:relative;}` +
        `${baseTd} .el-date-table-cell::after,${baseCell}::after{content:${content};position:absolute;top:1px;right:1px;min-width:14px;height:14px;padding:0 4px;border-radius:999px;display:inline-flex;align-items:center;justify-content:center;font-size:10px;line-height:14px;color:#fff;font-weight:700;background:var(--el-color-danger);pointer-events:none;}` +
        `${disabledTd} .el-date-table-cell::after,${disabledCell}::after{background:none;color:var(--el-color-danger);padding:0;min-width:auto;height:auto;line-height:11px;font-size:11px;}`
    )
  }
  return rules.join('\n')
})

const applyBatchPresetRange = () => {
  const end = new Date()
  const start = new Date(end.getTime())
  if (batchRangePreset.value === 'week') {
    start.setDate(end.getDate() - 6)
  } else if (batchRangePreset.value === 'month') {
    start.setDate(end.getDate() - 29)
  } else {
    return
  }
  batchDateRange.value = [formatLocalDate(start), formatLocalDate(end)]
}

const getBatchFilterPayload = () => {
  const range = Array.isArray(batchDateRange.value) ? batchDateRange.value : []
  const [dateStart, dateEnd] = range
  const payload = {}
  if (dateStart) payload.date_start = dateStart
  if (dateEnd) payload.date_end = dateEnd
  return payload
}

const generateForm = reactive({
  customer_id: '',
  employee_id: '',
  date_range: null,
  task_ids: [],
  invoice_date: new Date().toISOString().split('T')[0],
  is_paid: false
})

const generateRules = {
  customer_id: [{ required: true, message: t('invoice.customerRequired'), trigger: 'change' }],
  employee_id: [{ required: true, message: t('invoice.employeeRequired'), trigger: 'change' }],
  date_range: [{ required: true, message: t('invoice.dateRangeRequired'), trigger: 'change' }],
  task_ids: [{ required: true, message: t('invoice.taskRequired'), trigger: 'change' }]
}

const editForm = reactive({
  id: '',
  invoice_number: '',
  customer_id: '',
  invoice_date: '',
  items: []
})

const editRules = {
  customer_id: [{ required: true, message: t('invoice.customerRequired'), trigger: 'change' }],
  invoice_date: [{ required: true, message: t('invoice.invoiceDateRequired'), trigger: 'change' }]
}

const loadBatchPreview = async () => {
  batchPreviewLoading.value = true
  try {
    const res = await getUninvoicedTasksDetail(getBatchFilterPayload())
    const tasks = Array.isArray(res?.tasks)
      ? res.tasks
      : (Array.isArray(res?.data?.tasks) ? res.data.tasks : (Array.isArray(res) ? res : []))
    batchPreviewTasks.value = tasks
  } catch (error) {
    batchPreviewTasks.value = []
  } finally {
    batchPreviewLoading.value = false
  }
}

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

const serviceFilter = reactive({
  level1_id: '',
  level2_id: '',
  level3_id: ''
})

const serviceShowInactive = ref(false)
const serviceLevel1Options = ref([])
const serviceLevel2Options = ref([])
const serviceLevel3Options = ref([])
const serviceCodeRows = ref([])

const serviceLoading = reactive({
  level1: false,
  level2: false,
  level3: false,
  codes: false
})

const currentServiceLevel1 = computed(() => serviceLevel1Options.value.find((o) => o.id === serviceFilter.level1_id) || null)
const currentServiceLevel2 = computed(() => serviceLevel2Options.value.find((o) => o.id === serviceFilter.level2_id) || null)
const currentServiceLevel3 = computed(() => serviceLevel3Options.value.find((o) => o.id === serviceFilter.level3_id) || null)

const serviceLevelDialogVisible = ref(false)
const serviceLevelDialogSaving = ref(false)
const serviceLevelDialogType = ref('level1')
const serviceLevelDialogEditingId = ref(null)
const serviceLevelDialogFormRef = ref(null)
const serviceLevelDialogForm = reactive({
  name: ''
})

const serviceLevelDialogTitle = computed(() => {
  const typeMap = { level1: '一级', level2: '二级', level3: '三级' }
  const tName = typeMap[serviceLevelDialogType.value] || ''
  return serviceLevelDialogEditingId.value ? `编辑${tName}` : `新增${tName}`
})

const serviceRuleDialogVisible = ref(false)
const serviceRuleDialogSaving = ref(false)
const serviceRuleFormRef = ref(null)
const ruleLevel2Options = ref([])
const ruleLevel3Options = ref([])
const serviceRuleForm = reactive({
  id: null,
  level1_mode: 'select',
  level1_id: '',
  level1_name: '',
  level2_mode: 'none',
  level2_id: '',
  level2_name: '',
  level3_mode: 'select',
  level3_id: '',
  level3_name: '',
  code: '',
  description: '',
  unit_price: null
})

const serviceRuleDialogTitle = computed(() => {
  return serviceRuleForm.id ? '编辑服务条例' : '新增服务条例'
})

const getIdFromResponse = (res) => {
  const payload = res?.data ?? res
  return payload?.id ?? payload?.data?.id ?? payload?.result?.id ?? null
}

const getErrorDetail = (e) => {
  return e?.response?.data?.detail || e?.response?.data?.message || e?.message || ''
}

const isDuplicateNameError = (msg) => {
  if (!msg) return false
  const s = String(msg)
  return s.includes('已存在') || s.toLowerCase().includes('already exist')
}

const normalizeServiceLevelRows = (res) => {
  const rows = getArrayFromResponse(res)
  return rows
    .map((item) => ({
      id: item?.id ?? item?.value ?? item?.key,
      name: item?.name ?? item?.label ?? item?.title ?? item?.text ?? '',
      is_active: item?.is_active ?? item?.isActive ?? item?.active ?? true
    }))
    .filter((i) => i.id !== undefined && i.id !== null && i.name)
    .sort((a, b) => Number(a.is_active === false) - Number(b.is_active === false))
}

const parseAmountValue = (value) => {
  if (value == null) return null
  if (typeof value === 'number') return isNaN(value) ? null : value
  if (typeof value === 'string') {
    const s = value.trim()
    if (!s) return null
    const n = Number(s)
    return isNaN(n) ? null : n
  }
  if (typeof value === 'object') {
    const v = value?.value ?? value?.amount ?? value?.unit_price ?? value?.price ?? null
    return parseAmountValue(v)
  }
  return null
}

const normalizeServiceCodeRows = (res, level3Id = '') => {
  const rows = getArrayFromResponse(res)
  return rows
    .map((item) => {
      const code = item?.code || item?.service_code || item?.price_code || item?.priceCode || ''
      const description = item?.description || item?.name || ''
      const unit = parseAmountValue(item?.unit_price ?? item?.unitPrice ?? item?.price ?? item?.unit_price_aud ?? item?.default_unit_price ?? item?.unitPriceAUD)
      return {
        id: item?.id ?? item?.code_id ?? item?.codeId,
        level1_id: serviceFilter.level1_id || '',
        level2_id: serviceFilter.level2_id || '',
        level3_id: level3Id || serviceFilter.level3_id || '',
        code,
        description,
        unit_price: unit != null && !isNaN(unit) ? unit : 0,
        is_active: item?.is_active ?? item?.isActive ?? item?.active ?? true
      }
    })
    .filter((i) => i.id !== undefined && i.id !== null && i.code)
}

const tryResolveExistingServiceLevelId = async (type, name, ctx = {}) => {
  const n = (name || '').trim()
  if (!n) return null

  if (type === 'level1') {
    const res = await getServiceLevel1({ include_inactive: true })
    const rows = normalizeServiceLevelRows(res)
    const hit = rows.find((r) => String(r.name).trim() === n)
    if (!hit) return null
    if (hit.is_active === false) {
      await updateServiceLevel1(hit.id, { name: n, is_active: true }).catch(() => {})
    }
    return hit.id
  }

  if (type === 'level2') {
    if (!ctx?.level1_id) return null
    const res = await getServiceLevel2(ctx.level1_id, { include_inactive: true })
    const rows = normalizeServiceLevelRows(res)
    const hit = rows.find((r) => String(r.name).trim() === n)
    if (!hit) return null
    if (hit.is_active === false) {
      await updateServiceLevel2(hit.id, { name: n, is_active: true }).catch(() => {})
    }
    return hit.id
  }

  if (type === 'level3') {
    if (!ctx?.level1_id) return null
    const params = { level1_id: ctx.level1_id, include_inactive: true }
    if (ctx?.level2_id) params.level2_id = ctx.level2_id
    const res = await getServiceLevel3(params)
    const rows = normalizeServiceLevelRows(res)
    const hit = rows.find((r) => String(r.name).trim() === n)
    if (!hit) return null
    if (hit.is_active === false) {
      await updateServiceLevel3(hit.id, { name: n, is_active: true }).catch(() => {})
    }
    return hit.id
  }

  return null
}

const createServiceLevelWithFallback = async (type, payload, ctx = {}) => {
  try {
    if (type === 'level1') return getIdFromResponse(await createServiceLevel1(payload))
    if (type === 'level2') return getIdFromResponse(await createServiceLevel2(payload))
    if (type === 'level3') return getIdFromResponse(await createServiceLevel3(payload))
    return null
  } catch (e) {
    const msg = getErrorDetail(e)
    if (!isDuplicateNameError(msg)) throw e
    const existingId = await tryResolveExistingServiceLevelId(type, payload?.name, ctx)
    if (existingId == null) throw e
    return existingId
  }
}

const loadServiceLevel1Options = async () => {
  serviceLoading.level1 = true
  try {
    const params = serviceShowInactive.value ? { include_inactive: true } : {}
    const res = await getServiceLevel1(params)
    serviceLevel1Options.value = normalizeServiceLevelRows(res)
  } catch (e) {
    serviceLevel1Options.value = []
  } finally {
    serviceLoading.level1 = false
  }
}

const loadServiceLevel2Options = async (level1Id) => {
  serviceLoading.level2 = true
  try {
    if (!level1Id) {
      serviceLevel2Options.value = []
      return
    }
    const params = serviceShowInactive.value ? { include_inactive: true } : {}
    const res = await getServiceLevel2(level1Id, params)
    serviceLevel2Options.value = normalizeServiceLevelRows(res)
  } catch (e) {
    serviceLevel2Options.value = []
  } finally {
    serviceLoading.level2 = false
  }
}

const loadServiceLevel3Options = async (params) => {
  serviceLoading.level3 = true
  try {
    if (!params?.level1_id) {
      serviceLevel3Options.value = []
      return
    }
    const merged = { ...params }
    if (serviceShowInactive.value) merged.include_inactive = true
    const res = await getServiceLevel3(merged)
    serviceLevel3Options.value = normalizeServiceLevelRows(res)
  } catch (e) {
    serviceLevel3Options.value = []
  } finally {
    serviceLoading.level3 = false
  }
}

const loadServiceCodes = async (level3Id) => {
  serviceLoading.codes = true
  try {
    if (!level3Id) {
      serviceCodeRows.value = []
      return
    }
    const params = serviceShowInactive.value ? { include_inactive: true } : {}
    const res = await getServiceCodes(level3Id, params)
    serviceCodeRows.value = normalizeServiceCodeRows(res, level3Id)
  } catch (e) {
    serviceCodeRows.value = []
  } finally {
    serviceLoading.codes = false
  }
}

const handleServiceLevel1Change = async () => {
  serviceFilter.level2_id = ''
  serviceFilter.level3_id = ''
  serviceCodeRows.value = []
  await loadServiceLevel2Options(serviceFilter.level1_id)
  await loadServiceLevel3Options({ level1_id: serviceFilter.level1_id })
}

const handleServiceLevel2Change = async () => {
  serviceFilter.level3_id = ''
  serviceCodeRows.value = []
  const params = { level1_id: serviceFilter.level1_id }
  if (serviceFilter.level2_id) params.level2_id = serviceFilter.level2_id
  await loadServiceLevel3Options(params)
}

const handleServiceLevel3Change = async () => {
  await loadServiceCodes(serviceFilter.level3_id)
}

const reloadServiceAll = async () => {
  await loadServiceLevel1Options()
  if (serviceFilter.level1_id) {
    await loadServiceLevel2Options(serviceFilter.level1_id)
    const params = { level1_id: serviceFilter.level1_id }
    if (serviceFilter.level2_id) params.level2_id = serviceFilter.level2_id
    await loadServiceLevel3Options(params)
  } else {
    serviceLevel2Options.value = []
    serviceLevel3Options.value = []
  }
  if (serviceFilter.level3_id) {
    await loadServiceCodes(serviceFilter.level3_id)
  } else {
    serviceCodeRows.value = []
  }
}

const openServiceLevelDialog = (type, id) => {
  serviceLevelDialogType.value = type
  serviceLevelDialogEditingId.value = id || null
  if (id) {
    if (type === 'level1') {
      serviceLevelDialogForm.name = currentServiceLevel1.value?.name || ''
    } else if (type === 'level2') {
      serviceLevelDialogForm.name = currentServiceLevel2.value?.name || ''
    } else {
      serviceLevelDialogForm.name = currentServiceLevel3.value?.name || ''
    }
  } else {
    serviceLevelDialogForm.name = ''
  }
  serviceLevelDialogVisible.value = true
}

const saveServiceLevel = async () => {
  const name = (serviceLevelDialogForm.name || '').trim()
  if (!name) {
    ElMessage.error('请输入名称')
    return
  }
  if (serviceLevelDialogType.value !== 'level1' && !serviceFilter.level1_id) {
    ElMessage.error('请先选择一级')
    return
  }
  if (serviceLevelDialogType.value === 'level3' && !serviceFilter.level1_id) {
    ElMessage.error('请先选择一级')
    return
  }

  serviceLevelDialogSaving.value = true
  try {
    if (serviceLevelDialogType.value === 'level1') {
      if (serviceLevelDialogEditingId.value) {
        await updateServiceLevel1(serviceLevelDialogEditingId.value, { name })
      } else {
        const newId = await createServiceLevelWithFallback('level1', { name }, {})
        await loadServiceLevel1Options()
        if (newId != null) {
          serviceFilter.level1_id = newId
          await handleServiceLevel1Change()
        }
      }
    } else if (serviceLevelDialogType.value === 'level2') {
      if (serviceLevelDialogEditingId.value) {
        await updateServiceLevel2(serviceLevelDialogEditingId.value, { name })
      } else {
        const newId = await createServiceLevelWithFallback('level2', { level1_id: serviceFilter.level1_id, name }, { level1_id: serviceFilter.level1_id })
        await loadServiceLevel2Options(serviceFilter.level1_id)
        if (newId != null) {
          serviceFilter.level2_id = newId
          await handleServiceLevel2Change()
        }
      }
    } else {
      if (serviceLevelDialogEditingId.value) {
        await updateServiceLevel3(serviceLevelDialogEditingId.value, { name })
      } else {
        const payload = { level1_id: serviceFilter.level1_id, name }
        if (serviceFilter.level2_id) payload.level2_id = serviceFilter.level2_id
        const newId = await createServiceLevelWithFallback('level3', payload, { level1_id: serviceFilter.level1_id, level2_id: serviceFilter.level2_id || '' })
        const params = { level1_id: serviceFilter.level1_id }
        if (serviceFilter.level2_id) params.level2_id = serviceFilter.level2_id
        await loadServiceLevel3Options(params)
        if (newId != null) {
          serviceFilter.level3_id = newId
          await handleServiceLevel3Change()
        }
      }
    }

    if (serviceLevelDialogEditingId.value) {
      await reloadServiceAll()
    }
    ElMessage.success('保存成功')
    serviceLevelDialogVisible.value = false
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    serviceLevelDialogSaving.value = false
  }
}

const handleDeleteServiceLevel = async (type, id) => {
  try {
    await ElMessageBox.confirm('确定删除吗？', t('task.tip') || '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    if (type === 'level1') {
      await deleteServiceLevel1(id)
      if (serviceFilter.level1_id === id) {
        serviceFilter.level1_id = ''
        serviceFilter.level2_id = ''
        serviceFilter.level3_id = ''
      }
    } else if (type === 'level2') {
      await deleteServiceLevel2(id)
      if (serviceFilter.level2_id === id) {
        serviceFilter.level2_id = ''
        serviceFilter.level3_id = ''
      }
    } else {
      await deleteServiceLevel3(id)
      if (serviceFilter.level3_id === id) {
        serviceFilter.level3_id = ''
      }
    }
    await reloadServiceAll()
    ElMessage.success('删除成功')
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '删除失败'
    ElMessage.error(msg)
  }
}

const resetServiceRuleForm = () => {
  serviceRuleForm.id = null
  serviceRuleForm.level1_mode = 'select'
  serviceRuleForm.level1_id = serviceFilter.level1_id || ''
  serviceRuleForm.level1_name = ''
  serviceRuleForm.level2_mode = serviceFilter.level2_id ? 'select' : 'none'
  serviceRuleForm.level2_id = serviceFilter.level2_id || ''
  serviceRuleForm.level2_name = ''
  serviceRuleForm.level3_mode = 'select'
  serviceRuleForm.level3_id = serviceFilter.level3_id || ''
  serviceRuleForm.level3_name = ''
  serviceRuleForm.code = ''
  serviceRuleForm.description = ''
  serviceRuleForm.unit_price = null
  ruleLevel2Options.value = []
  ruleLevel3Options.value = []
}

const loadRuleLevel2 = async (level1Id) => {
  if (!level1Id) {
    ruleLevel2Options.value = []
    return
  }
  try {
    const res = await getServiceLevel2(level1Id)
    ruleLevel2Options.value = normalizeServiceLevelRows(res)
  } catch (e) {
    ruleLevel2Options.value = []
  }
}

const loadRuleLevel3 = async (params) => {
  if (!params?.level1_id) {
    ruleLevel3Options.value = []
    return
  }
  try {
    const res = await getServiceLevel3(params)
    ruleLevel3Options.value = normalizeServiceLevelRows(res)
  } catch (e) {
    ruleLevel3Options.value = []
  }
}

const handleRuleLevel1Change = async () => {
  if (serviceRuleForm.level1_mode !== 'select') return
  serviceRuleForm.level2_id = ''
  serviceRuleForm.level3_id = ''
  await loadRuleLevel2(serviceRuleForm.level1_id)
  await loadRuleLevel3({ level1_id: serviceRuleForm.level1_id })
}

const handleRuleLevel2Change = async () => {
  if (serviceRuleForm.level1_mode !== 'select') return
  serviceRuleForm.level3_id = ''
  const params = { level1_id: serviceRuleForm.level1_id }
  if (serviceRuleForm.level2_mode === 'select' && serviceRuleForm.level2_id) params.level2_id = serviceRuleForm.level2_id
  await loadRuleLevel3(params)
}

const handleRuleLevel3Change = async () => {}

const openServiceRuleDialog = async (row) => {
  resetServiceRuleForm()
  if (row?.id != null) {
    serviceRuleForm.id = row.id
    serviceRuleForm.code = row.code || ''
    serviceRuleForm.description = row.description || ''
    serviceRuleForm.unit_price = row.unit_price != null ? Number(row.unit_price) : (row.price != null ? Number(row.price) : null)
    serviceRuleForm.level1_id = row.level1_id || serviceFilter.level1_id || ''
    serviceRuleForm.level2_id = row.level2_id || serviceFilter.level2_id || ''
    serviceRuleForm.level3_id = row.level3_id || serviceFilter.level3_id || ''
    serviceRuleForm.level2_mode = serviceRuleForm.level2_id ? 'select' : 'none'
  }

  if (!serviceLevel1Options.value.length) {
    await loadServiceLevel1Options()
  }

  if (serviceRuleForm.level1_id) {
    await loadRuleLevel2(serviceRuleForm.level1_id)
    const params = { level1_id: serviceRuleForm.level1_id }
    if (serviceRuleForm.level2_id) params.level2_id = serviceRuleForm.level2_id
    await loadRuleLevel3(params)
  }

  serviceRuleDialogVisible.value = true
}

const ensureRuleLevel1Id = async () => {
  if (serviceRuleForm.level1_mode === 'select') return serviceRuleForm.level1_id || null
  const name = (serviceRuleForm.level1_name || '').trim()
  if (!name) return null
  const newId = await createServiceLevelWithFallback('level1', { name }, {})
  await loadServiceLevel1Options()
  return newId
}

const ensureRuleLevel2Id = async (level1Id) => {
  if (!level1Id) return null
  if (serviceRuleForm.level2_mode === 'none') return null
  if (serviceRuleForm.level2_mode === 'select') return serviceRuleForm.level2_id || null
  const name = (serviceRuleForm.level2_name || '').trim()
  if (!name) return null
  const newId = await createServiceLevelWithFallback('level2', { level1_id: level1Id, name }, { level1_id: level1Id })
  return newId
}

const ensureRuleLevel3Id = async (level1Id, level2Id) => {
  if (!level1Id) return null
  if (serviceRuleForm.level3_mode === 'select') return serviceRuleForm.level3_id || null
  const name = (serviceRuleForm.level3_name || '').trim()
  if (!name) return null
  const payload = { level1_id: level1Id, name }
  if (level2Id) payload.level2_id = level2Id
  const newId = await createServiceLevelWithFallback('level3', payload, { level1_id: level1Id, level2_id: level2Id || '' })
  return newId
}

const saveServiceRule = async () => {
  const code = (serviceRuleForm.code || '').trim()
  if (!code) {
    ElMessage.error('请输入服务编码')
    return
  }
  const unitPrice = serviceRuleForm.unit_price != null ? Number(serviceRuleForm.unit_price) : null
  if (unitPrice == null || isNaN(unitPrice) || unitPrice <= 0) {
    ElMessage.error('请输入单价')
    return
  }
  if (serviceRuleForm.level1_mode === 'select' && !serviceRuleForm.level1_id) {
    ElMessage.error('请选择一级')
    return
  }
  if (serviceRuleForm.level1_mode === 'new' && !(serviceRuleForm.level1_name || '').trim()) {
    ElMessage.error('请输入一级名称')
    return
  }
  if (serviceRuleForm.level2_mode === 'select' && !serviceRuleForm.level2_id) {
    ElMessage.error('请选择二级')
    return
  }
  if (serviceRuleForm.level2_mode === 'new' && !(serviceRuleForm.level2_name || '').trim()) {
    ElMessage.error('请输入二级名称')
    return
  }
  if (serviceRuleForm.level3_mode === 'select' && !serviceRuleForm.level3_id) {
    ElMessage.error('请选择三级')
    return
  }
  if (serviceRuleForm.level3_mode === 'new' && !(serviceRuleForm.level3_name || '').trim()) {
    ElMessage.error('请输入三级名称')
    return
  }

  serviceRuleDialogSaving.value = true
  try {
    const level1Id = await ensureRuleLevel1Id()
    if (!level1Id) {
      ElMessage.error('一级创建失败')
      return
    }
    const level2Id = await ensureRuleLevel2Id(level1Id)
    const level3Id = await ensureRuleLevel3Id(level1Id, level2Id)
    if (!level3Id) {
      ElMessage.error('三级创建失败')
      return
    }

    const payload = {
      level3_id: level3Id,
      code,
      description: serviceRuleForm.description || '',
      // 兼容后端字段：同时传 price 与 unit_price，且使用数值类型
      price: Number(unitPrice),
      unit_price: Number(unitPrice)
    }

    if (serviceRuleForm.id) {
      await updateServiceCode(serviceRuleForm.id, payload)
    } else {
      await createServiceCode(payload)
    }

    serviceFilter.level1_id = level1Id
    serviceFilter.level2_id = level2Id || ''
    serviceFilter.level3_id = level3Id
    await reloadServiceAll()
    ElMessage.success('保存成功')
    serviceRuleDialogVisible.value = false
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '保存失败'
    ElMessage.error(msg)
  } finally {
    serviceRuleDialogSaving.value = false
  }
}

const handleDeleteServiceCode = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除该服务编码吗？', t('task.tip') || '提示', { type: 'warning' })
  } catch (e) {
    return
  }
  try {
    await deleteServiceCode(row.id)
    await loadServiceCodes(serviceFilter.level3_id)
    ElMessage.success('删除成功')
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '删除失败'
    ElMessage.error(msg)
  }
}

const loadInvoices = async () => {
  loading.value = true
  try {
    const res = await getInvoices()
    invoices.value = getArrayFromResponse(res)
  } catch (error) {
    ElMessage.error(t('invoice.loadInvoicesFailed'))
  } finally {
    loading.value = false
  }
}

const loadUnissuedTasks = async () => {
  loadingUnissued.value = true
  try {
    const rows = await getTasksForInvoice()
    unissuedTasks.value = getArrayFromResponse(rows).map((r) => ({
      ...r,
      id: r?.id ?? r?.task_id ?? r?.taskId
    }))
  } catch {
    unissuedTasks.value = []
  } finally {
    loadingUnissued.value = false
  }
}

const loadCustomers = async () => {
  try {
    customers.value = await getCustomers()
  } catch (error) {
    ElMessage.error(t('invoice.loadCustomersFailed'))
  }
}

const loadEmployees = async () => {
  try {
    employees.value = await getEmployees()
  } catch (error) {
    ElMessage.error(t('invoice.loadEmployeesFailed'))
  }
}

const loadTasks = async (params = {}) => {
  loadingTasks.value = true
  try {
    // 构建查询参数
    const queryParams = {}
    if (params.customer_id) {
      queryParams.customer_id = params.customer_id
    }
    if (params.employee_id) {
      queryParams.employee_id = params.employee_id
    }
    if (params.date_start) {
      queryParams.date_start = params.date_start
    }
    if (params.date_end) {
      queryParams.date_end = params.date_end
    }
    
    const result = await getTasksForInvoice(queryParams)
    tasks.value = getArrayFromResponse(result).map((r) => ({
      ...r,
      id: r?.id ?? r?.task_id ?? r?.taskId
    }))
    const availableIds = new Set(tasks.value.map((task) => task.id))
    const currentSelection = Array.isArray(generateForm.task_ids) ? generateForm.task_ids : []
    const nextSelection = currentSelection.filter((id) => availableIds.has(id))

    if (tasks.value.length === 1) {
      generateForm.task_ids = [tasks.value[0].id]
    } else {
      generateForm.task_ids = nextSelection
    }

    syncSelectedTaskItems()
  } catch (error) {
    console.error('加载任务失败:', error)
    // 静默处理错误，不显示错误消息（避免干扰用户操作）
    tasks.value = []
    generateForm.task_ids = []
    syncSelectedTaskItems()
  } finally {
    loadingTasks.value = false
  }
}

const handleGenerate = async () => {
  if (!generateFormRef.value) return
  await generateFormRef.value.validate(async (valid) => {
    if (valid) {
      const invalidItem = selectedTaskItems.value.find(
        (item) =>
          item.price === null ||
          item.price === undefined ||
          item.quantity === null ||
          item.quantity === undefined ||
          Number(item.price || 0) <= 0 ||
          Number(item.quantity || 0) <= 0
      )
      if (invalidItem) {
        ElMessage.error(t('invoice.priceQuantityRequired'))
        return
      }
      try {
        // 格式化日期
        const requestData = {
          customer_id: generateForm.customer_id,
          employee_id: generateForm.employee_id,
          task_ids: generateForm.task_ids,
          is_paid: !!generateForm.is_paid,
          task_overrides: selectedTaskItems.value.map((item) => ({
            task_id: item.task_id,
            price: item.price,
            quantity: item.quantity
          })),
          invoice_date: generateForm.invoice_date
        }
        
        // 处理日期范围
        if (generateForm.date_range && generateForm.date_range.length === 2) {
          requestData.date_start = generateForm.date_range[0]
          requestData.date_end = generateForm.date_range[1]
        }
        
        // 处理发票日期 - 转换为ISO格式
        if (requestData.invoice_date) {
          requestData.invoice_date = `${requestData.invoice_date}T00:00:00.000Z`
        }
        
        await generateInvoice(requestData)
        ElMessage.success(t('invoice.generateSuccess'))
        showGenerateDialog.value = false
        // 重置表单
        generateForm.customer_id = ''
        generateForm.employee_id = ''
        generateForm.date_range = null
        generateForm.task_ids = []
        generateForm.invoice_date = new Date().toISOString().split('T')[0]
        generateForm.is_paid = false
        selectedTaskItems.value = []
        loadInvoices()
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || t('invoice.generateFailed')
        ElMessage.error(errorMessage)
      }
    }
  })
}

const handleView = (row) => {
  router.push(`/invoices/${row.id}`)
}

const resetEditForm = () => {
  editForm.id = ''
  editForm.invoice_number = ''
  editForm.customer_id = ''
  editForm.invoice_date = ''
  editForm.items = []
}

const formatAmount = (row) => {
  const price = Number(row.price || 0)
  const quantity = Number(row.quantity || 0)
  return (price * quantity).toFixed(2)
}

const formatAmountNumber = (num) => {
  const n = Number(num || 0)
  return n.toFixed(2)
}

const syncSelectedTaskItems = () => {
  const selectedIds = new Set(generateForm.task_ids || [])
  const taskMap = new Map(tasks.value.map((task) => [task.id, task]))
  const existingMap = new Map(selectedTaskItems.value.map((item) => [item.task_id, item]))
  const nextItems = []

  selectedIds.forEach((id) => {
    const existing = existingMap.get(id)
    const task = taskMap.get(id)
    if (existing) {
      if (task) {
        existing.title = task.title
        existing.service_code = task.service_code
      }
      nextItems.push(existing)
    } else {
      nextItems.push({
        task_id: id,
        title: task?.title || id,
        service_code: task?.service_code || '',
        price: null,
        quantity: 1
      })
    }
  })

  selectedTaskItems.value = nextItems
}

const getUnissuedServiceCodes = (row) => {
  const rawList = Array.isArray(row?.services) ? row.services : (Array.isArray(row?.service_items) ? row.service_items : [])
  const list = rawList.map((s) => s?.service_code || s?.code || '').filter(Boolean)
  const fallback = row?.service_code ? [row.service_code] : []
  const normalized = (list.length ? list : fallback).map((c) => String(c).trim()).filter(Boolean)
  return Array.from(new Set(normalized))
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

const normalizeServiceLine = (line, fallbackIndex = 0) => {
  const unitRaw =
    line?.unit_price_override ??
    line?.unit_price ??
    line?.price ??
    line?.unitPrice ??
    null
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

  const unitPrice = unitRaw != null && !isNaN(Number(unitRaw)) ? Number(unitRaw) : null
  const quantity = qtyRaw != null && !isNaN(Number(qtyRaw)) ? Number(qtyRaw) : null
  const amountDirect = amountRaw != null && !isNaN(Number(amountRaw)) ? Number(amountRaw) : null
  const amountDerived = unitPrice != null && quantity != null ? Number((unitPrice * quantity).toFixed(2)) : null

  const start = line?.service_time_start || line?.service_start_time || line?.serviceTimeStart || ''
  const end = line?.service_time_end || line?.service_end_time || line?.serviceTimeEnd || ''

  return {
    id: line?.id ?? `line_${fallbackIndex}`,
    description: line?.description || line?.remark || line?.service_name || line?.name || '',
    code: line?.code || line?.service_code || line?.serviceCode || '',
    service_code: line?.service_code || line?.code || line?.serviceCode || '',
    unit_price: unitPrice != null ? unitPrice : 0,
    quantity: quantity != null ? quantity : 0,
    amount: amountDirect != null ? amountDirect : (amountDerived != null ? amountDerived : 0),
    service_time_start: start === '0000' ? '' : start,
    service_time_end: end === '0000' ? '' : end
  }
}

const buildServiceLinesFromTaskDetail = (taskDetail) => {
  const list = Array.isArray(taskDetail?.services)
    ? taskDetail.services
    : (Array.isArray(taskDetail?.service_items) ? taskDetail.service_items : [])
  return list.map((s, idx) => {
    const line = normalizeServiceLine(s, idx)
    if (!line.description) {
      line.description = taskDetail?.title || taskDetail?.id || ''
    }
    if (!line.code) {
      line.code = line.service_code || ''
    }
    return line
  })
}

const normalizeUnissuedDetail = (detail) => {
  const payload = detail?.data ?? detail
  const task = payload?.task || null
  const customer = payload?.customer || null
  const employee = payload?.employee || payload?.assigned_employee || null
  const serviceLinesRaw = payload?.service_lines || payload?.serviceLines || payload?.services || payload?.service_items || []
  const serviceLinesList = Array.isArray(serviceLinesRaw) ? serviceLinesRaw : []
  const service_lines = serviceLinesList.map((l, idx) => normalizeServiceLine(l, idx))
  const totalAmountRaw = payload?.total_amount ?? payload?.totalAmount ?? 0
  const totalDirect = totalAmountRaw != null && !isNaN(Number(totalAmountRaw)) ? Number(totalAmountRaw) : null
  const totalDerived = service_lines.reduce((sum, l) => sum + Number(l.amount || 0), 0)
  const totalAmount = totalDirect != null ? totalDirect : Number(totalDerived.toFixed(2))
  return {
    task,
    customer,
    employee,
    service_lines,
    total_amount: totalAmount
  }
}

const openGenerateForTask = async (task) => {
  const tid = getRowTaskId(task)
  if (!tid) return
  unissuedTaskId.value = tid
  unissuedIsPaid.value = false
  unissuedPreview.value = {
    task: { id: tid, title: task?.title || tid },
    customer: task?.customer || (task?.customer_name ? { name: task.customer_name } : null),
    employee:
      task?.employee ||
      task?.assigned_employee ||
      (task?.employee_name ? { name: task.employee_name } : (task?.assigned_employee_name ? { name: task.assigned_employee_name } : null)),
    service_lines: [],
    total_amount: getUnissuedTotalAmount(task)
  }
  showUnissuedGenerateDialog.value = true
  unissuedPreviewLoading.value = true
  try {
    const [detailRes, taskRes] = await Promise.allSettled([getInvoiceTaskDetail(tid), getTask(tid)])
    const normalized = detailRes.status === 'fulfilled' ? normalizeUnissuedDetail(detailRes.value) : null
    const taskDetail = taskRes.status === 'fulfilled' ? (taskRes.value?.data ?? taskRes.value) : null
    const taskLines = taskDetail ? buildServiceLinesFromTaskDetail(taskDetail) : []

    const preferredLines = taskLines.length ? taskLines : (normalized?.service_lines || [])
    const customerPreferred = taskDetail?.customer || normalized?.customer || unissuedPreview.value.customer
    const employeePreferred =
      taskDetail?.assigned_employee ||
      taskDetail?.employee ||
      normalized?.employee ||
      unissuedPreview.value.employee
    const totalAmount =
      preferredLines.reduce((sum, l) => sum + Number(l.amount || 0), 0) ||
      normalized?.total_amount ||
      unissuedPreview.value.total_amount ||
      0

    unissuedPreview.value = {
      task: taskDetail || normalized?.task || unissuedPreview.value.task,
      customer: customerPreferred,
      employee: employeePreferred,
      service_lines: preferredLines,
      total_amount: Number(totalAmount.toFixed(2))
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('invoice.generateFailed'))
    showUnissuedGenerateDialog.value = false
  } finally {
    unissuedPreviewLoading.value = false
  }
}

const confirmUnissuedGenerate = async () => {
  if (!unissuedTaskId.value) return
  try {
    unissuedGenerating.value = true
    const lines = Array.isArray(unissuedPreview.value?.service_lines) ? unissuedPreview.value.service_lines : []
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
    const payload = {
      customer_id: unissuedPreview.value?.customer?.id || null,
      employee_id: unissuedPreview.value?.employee?.id || null,
      invoice_date: unissuedPreview.value?.task?.service_time ? fmtDate(unissuedPreview.value.task.service_time) : (new Date().toISOString().split('T')[0]),
      is_paid: !!unissuedIsPaid.value,
      items: lines.map((l) => {
        const unit = l?.unit_price != null ? Number(l.unit_price) : (l?.price != null ? Number(l.price) : 0)
        const qty = l?.quantity != null ? Number(l.quantity) : (l?.duration_hours != null ? Number(l.duration_hours) : 0)
        const amt = l?.amount != null ? Number(l.amount) : Number((unit * qty).toFixed(2))
        return {
          task_service_item_id: l?.task_service_item_id || l?.id || null,
          description: l?.description || '',
          code: l?.service_code || l?.code || '',
          unit_price: unit,
          quantity: qty,
          amount: amt,
          service_date: l?.service_date || fmtDate(l?.service_time_start || ''),
          service_time_start: fmtHHmm(l?.service_time_start || ''),
          service_time_end: fmtHHmm(l?.service_time_end || '')
        }
      })
    }
    const res = await generateInvoiceForTask(unissuedTaskId.value, payload)
    ElMessage.success(t('invoice.generateSuccess'))
    showUnissuedGenerateDialog.value = false
    await Promise.all([loadInvoices(), loadUnissuedTasks()])
    const id = res?.id || res?.invoice_id || res?.invoiceId
    if (id) {
      try {
        const detail = await getInvoiceTaskDetail(unissuedTaskId.value)
        const normalized = normalizeUnissuedDetail(detail)
        const toItems = (normalized.service_lines || []).map((line) => {
          const start = line?.service_time_start || ''
          const end = line?.service_time_end || ''
          const datePart = start && typeof start === 'string' ? (start.split(' ')[0] || '') : ''
          const hhmm = (s) => {
            if (!s || typeof s !== 'string') return ''
            if (/^\d{4}$/.test(s)) return s
            const t = s.includes(' ') ? s.split(' ')[1] || '' : s
            const hh = t.slice(0, 2)
            const mm = t.slice(3, 5)
            return hh && mm ? `${hh}${mm}` : ''
          }
          const unit =
            line?.unit_price != null ? Number(line.unit_price) : (line?.price != null ? Number(line.price) : 0)
          const qty =
            line?.quantity != null ? Number(line.quantity) :
            (line?.duration_hours != null ? Number(line.duration_hours) : 0)
          const amount =
            line?.amount != null ? Number(line.amount) : Number((unit * qty).toFixed(2))
          return {
            task_id: normalized.task?.id || unissuedTaskId.value,
            description: line?.description || normalized.task?.title || normalized.task?.id || '',
            service_code: line?.service_code || line?.code || '',
            price: unit,
            quantity: qty,
            service_date: datePart,
            service_time_start: hhmm(start),
            service_time_end: hhmm(end),
            amount
          }
        })
        const invDateSrc = normalized.task?.service_time || ''
        const invDate = invDateSrc && typeof invDateSrc === 'string'
          ? (invDateSrc.split(' ')[0] || '')
          : new Date().toISOString().split('T')[0]
        await updateInvoice(id, {
          customer_id: normalized.customer?.id || null,
          invoice_date: `${invDate}T00:00:00.000Z`,
          items: toItems
        })
      } catch {}
      router.push(`/invoices/${id}`)
    }
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || t('invoice.generateFailed'))
  } finally {
    unissuedGenerating.value = false
  }
}

const handleAddEditItem = () => {
  editForm.items.push({
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

const handleRemoveEditItem = (index) => {
  editForm.items.splice(index, 1)
}

const handleEdit = async (row) => {
  editLoading.value = true
  try {
    const invoice = await getInvoice(row.id)
    editForm.id = invoice.id
    editForm.invoice_number = invoice.invoice_number
    editForm.customer_id = invoice.customer_id
    editForm.invoice_date = invoice.invoice_date ? formatDate(invoice.invoice_date, 'YYYY-MM-DD') : ''
    editForm.items = (invoice.items || []).map((item) => ({
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
    if (editForm.items.length === 0) {
      handleAddEditItem()
    }
    showEditDialog.value = true
  } catch (error) {
    const errorMessage = error.response?.data?.detail || error.message || t('invoice.loadInvoiceFailed')
    ElMessage.error(errorMessage)
  } finally {
    editLoading.value = false
  }
}

const handleUpdate = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    if (!editForm.items.length) {
      ElMessage.error(t('invoice.itemRequired'))
      return
    }

    const missingDesc = editForm.items.find((item) => !item.description)
    if (missingDesc) {
      ElMessage.error(t('invoice.itemInvalid'))
      return
    }
    const invalidPriceQty = editForm.items.find(
      (item) => Number(item.price || 0) <= 0 || Number(item.quantity || 0) <= 0
    )
    if (invalidPriceQty) {
      ElMessage.error(t('invoice.priceQuantityRequired'))
      return
    }

    try {
      editLoading.value = true
      const payload = {
        customer_id: editForm.customer_id,
        invoice_date: editForm.invoice_date ? `${editForm.invoice_date}T00:00:00.000Z` : null,
        items: editForm.items.map((item) => ({
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
      await updateInvoice(editForm.id, payload)
      ElMessage.success(t('invoice.editSuccess'))
      showEditDialog.value = false
      resetEditForm()
      loadInvoices()
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || t('invoice.editFailed')
      ElMessage.error(errorMessage)
    } finally {
      editLoading.value = false
    }
  })
}

const handleSend = async (row) => {
  if (!row?.pdf_url) {
    ElMessage.warning(t('invoice.fileNotExists'))
    return
  }
  pendingSendType.value = 'single'
  pendingSendInvoiceRow.value = row
  sendLang.value = 'en'
  sendLangDialogVisible.value = true
}

const submitSendWithLang = async () => {
  sendLangSubmitting.value = true
  try {
    if (pendingSendType.value === 'batch') {
      await batchSendUnsentInvoices(null, sendLang.value)
      ElMessage.success(t('invoice.batchSendSuccess'))
      await loadInvoices()
      sendLangDialogVisible.value = false
      return
    }

    const row = pendingSendInvoiceRow.value
    if (!row?.id) return
    const res = await sendInvoice(row.id, sendLang.value)
    const payload = res?.data ?? res
    const sentEmail = payload?.email ?? payload?.data?.email ?? payload?.result?.email ?? ''
    if (sentEmail) {
      ElMessage.success(`${t('invoice.invoiceSentSuccess')} ${sentEmail}`)
    } else {
      ElMessage.success(t('invoice.sendSuccess'))
    }
    sendLangDialogVisible.value = false
    await loadInvoices()
  } catch (error) {
    const errorMessage = error.response?.data?.detail || error.message || t('invoice.sendFailed')
    ElMessage.error(errorMessage)
  } finally {
    sendLangSubmitting.value = false
  }
}

const handleDelete = async (row) => {
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
    await Promise.all([loadInvoices(), loadUnissuedTasks()])
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || t('invoice.deleteFailed'))
    }
  }
}

// 监听表单字段变化，自动加载服务代码
watch(
  () => [generateForm.customer_id, generateForm.employee_id, generateForm.date_range],
  ([customerId, employeeId, dateRange]) => {
    // 只有当客户、员工和日期范围都选择后才加载任务
    if (customerId && employeeId && dateRange && dateRange.length === 2) {
      const params = {
        customer_id: customerId,
        employee_id: employeeId,
        date_start: dateRange[0],
        date_end: dateRange[1]
      }
      loadTasks(params)
    } else {
      // 如果条件不满足，清空任务列表
      tasks.value = []
      generateForm.task_ids = []
      syncSelectedTaskItems()
    }
  },
  { deep: true }
)

watch(
  () => generateForm.task_ids,
  () => {
    syncSelectedTaskItems()
  },
  { deep: true }
)

// 监听对话框打开，重置表单
watch(showGenerateDialog, (newVal) => {
  if (newVal) {
    // 对话框打开时重置表单
    generateForm.customer_id = ''
    generateForm.employee_id = ''
    generateForm.date_range = null
    generateForm.task_ids = []
    generateForm.invoice_date = new Date().toISOString().split('T')[0]
    generateForm.is_paid = false
    tasks.value = []
    selectedTaskItems.value = []
  }
})

watch(showEditDialog, (newVal) => {
  if (!newVal) {
    resetEditForm()
  }
})

onMounted(() => {
  if (isServiceEditor.value) {
    reloadServiceAll()
    return
  }
  loadCustomers()
  loadEmployees()
  // 默认加载列表
  if (viewMode.value === 'issued') loadInvoices()
  if (viewMode.value === 'unissued') loadUnissuedTasks()
})

watch(showBatchGenerateDialog, async (val) => {
  if (val) {
    if (!Array.isArray(unissuedTasks.value) || unissuedTasks.value.length === 0) {
      await loadUnissuedTasks()
    }
    if (batchRangePreset.value !== 'custom') applyBatchPresetRange()
    await loadBatchPreview()
  }
})

watch(batchRangePreset, async () => {
  if (!showBatchGenerateDialog.value) return
  if (batchRangePreset.value !== 'custom') {
    applyBatchPresetRange()
  }
  await loadBatchPreview()
})

watch(
  () => batchDateRange.value,
  async () => {
    if (!showBatchGenerateDialog.value) return
    if (batchRangePreset.value !== 'custom') return
    await loadBatchPreview()
  },
  { deep: true }
)

watch(
  () => viewMode.value,
  (val) => {
    if (isServiceEditor.value) return
    if (val === 'issued') loadInvoices()
    if (val === 'unissued') loadUnissuedTasks()
  },
  { immediate: true }
)
const handleBatchSendUnsent = async () => {
  try {
    await ElMessageBox.confirm(t('invoice.batchSendConfirm'), t('invoice.title'), { type: 'warning' })
  } catch (e) {
    if (e === 'cancel' || e === 'close') return
  }
  pendingSendType.value = 'batch'
  pendingSendInvoiceRow.value = null
  sendLang.value = 'en'
  sendLangDialogVisible.value = true
}

const confirmBatchGenerate = async () => {
  batchGenerating.value = true
  try {
    const res = await batchGenerateUninvoiced(getBatchFilterPayload())
    const payload = res?.data ?? res
    const created = payload?.created ?? 0
    const customersCount = payload?.customers ?? 0
    ElMessage.success(`已生成 ${created} 张发票（客户数 ${customersCount}）`)
    showBatchGenerateDialog.value = false
    await Promise.all([loadUnissuedTasks(), loadInvoices()])
  } catch (error) {
    ElMessage.error(error?.response?.data?.detail || t('invoice.batchGenerateFailed'))
  } finally {
    batchGenerating.value = false
  }
}
</script>



<style scoped>
.invoice-list {
  padding: 20px;
}

.task-embed :deep(.task-list) {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pager-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.service-toolbar {
  display: flex;
  gap: 10px;
}

.service-filters {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

:deep(.service-filters .el-form-item) {
  margin-bottom: 0;
  margin-right: 0;
  width: 100%;
}

:deep(.service-filters .el-form-item__content) {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 768px) {
  .invoice-list {
    padding: 12px;
  }

  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .service-toolbar {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-start;
  }

  :deep(.service-toolbar .el-button) {
    flex: 0 0 auto;
  }

  :deep(.service-toolbar .el-switch) {
    flex: 1 1 100%;
  }

  .service-filters {
    gap: 14px;
  }

  :deep(.service-filters .el-form-item__content) {
    align-items: stretch;
  }

  :deep(.service-filters .el-form-item__content > .el-select) {
    width: 100% !important;
  }

  :deep(.service-filters .el-form-item__content .el-button) {
    flex: 1 1 30%;
  }
}

.edit-items-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.item-amount {
  font-weight: 600;
}

.task-option-title {
  font-weight: 500;
}

.task-option-id {
  color: var(--el-text-color-secondary);
  font-size: 16px;
  margin-left: 8px;
}

:deep(.uninvoiced-date-range-popper .el-date-table-cell) {
  position: relative;
}
</style>
