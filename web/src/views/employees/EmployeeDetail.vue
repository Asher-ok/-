<template>
  <div class="employee-detail">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ employee.name || '' }}</span>
          <div style="display: flex; align-items: center; gap: 10px;">
            <el-select
              v-model="accountStatusDraft"
              size="small"
              style="width: 120px;"
              @change="handleAccountStatusChange"
            >
              <el-option :label="$t('employee.accountStatusNormal')" value="normal" />
              <el-option :label="$t('employee.accountStatusDisabled')" value="disabled" />
            </el-select>
            <el-button @click="$router.back()">{{ $t('common.return') }}</el-button>
          </div>
        </div>
      </template>
      
      <div class="basic-info">
        <el-descriptions :column="isMobile ? 1 : 2" :direction="isMobile ? 'vertical' : 'horizontal'" border>
          <el-descriptions-item :label="$t('employee.name')">
            <span class="employee-name">{{ employee.name || '-' }}</span>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('employee.employeeNumber')">{{ employee.employee_number || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('employee.department')">{{ employee.department || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('employee.phone')">{{ employee.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('employee.email')">{{ employee.email || '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('employee.createTime')">{{ formatDate(employee.created_at) || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-tabs v-model="activeMenu" class="detail-tabs" @tab-change="handleTabChange">
        <el-tab-pane :label="$t('employee.contract')" name="contract" lazy>
          <div class="content-section">
            <div class="section-header section-header--right">
              <div>
                <el-button type="success" @click="showContractForm = true" style="margin-right: 10px;">
                  <el-icon><EditPen /></el-icon>
                  {{ $t('employee.generateContract') }}
                </el-button>
                <el-button type="primary" @click="handleUploadContract">
                  <el-icon><Upload /></el-icon>
                  {{ $t('employee.uploadContract') }}
                </el-button>
              </div>
            </div>
            <el-table :data="contractDocuments" stripe v-if="contractDocuments.length > 0" style="width: 100%; margin-top: 0" table-layout="auto">
              <el-table-column prop="name" :label="$t('employee.fileName')" width="330" show-overflow-tooltip />
              <el-table-column prop="file_type" :label="$t('employee.fileType')" width="170" align="center" />
              <el-table-column prop="uploaded_at" :label="$t('employee.uploadTime')" width="250" align="center">
                <template #default="{ row }">
                  {{ formatDate(row.uploaded_at) }}
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.signatureStatus')" min-width="260" align="center">
                <template #default="{ row }">
                  <div class="signature-status">
                    <el-tag :type="row.employee_signed_at ? 'success' : 'info'" size="small">
                      {{ $t('employee.signatureEmployee') }}: {{ row.employee_signed_at ? $t('employee.signatureSigned') : $t('employee.signatureUnsigned') }}
                    </el-tag>
                    <el-tag :type="row.admin_signed_at ? 'success' : 'info'" size="small">
                      {{ $t('employee.signatureAdmin') }}: {{ row.admin_signed_at ? $t('employee.signatureSigned') : $t('employee.signatureUnsigned') }}
                    </el-tag>
                  </div>
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.operations')" width="240" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
                <template #default="{ row }">
                  <div class="action-buttons action-buttons--scroll">
                    <div class="action-buttons-inner">
                      <el-button type="success" size="small" @click="handleViewDocument(row)">
                        {{ $t('common.view') }}
                      </el-button>
                      <el-button type="info" size="small" @click="handleSendContractSignLink(row)">
                        {{ $t('employee.sendContractSignLink') }}
                      </el-button>
                      <el-button type="warning" size="small" @click="handleStartSignContract(row)">
                        {{ $t('employee.sign') }}
                      </el-button>
                      <el-button type="danger" size="small" @click="handleDeleteDocument(row)">
                        {{ $t('common.delete') }}
                      </el-button>
                    </div>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else :description="$t('employee.noContract')" />
          </div>
        </el-tab-pane>

        <el-tab-pane :label="$t('employee.code')" name="code" lazy>
          <div class="content-section">
            <div class="section-header section-header--right">
              <el-button type="primary" @click="handleUploadCode">
                <el-icon><Upload /></el-icon>
                {{ $t('employee.uploadCode') }}
              </el-button>
            </div>
            <el-table :data="codeDocuments" stripe v-if="codeDocuments.length > 0" style="width: 100%; margin-top: 0" table-layout="auto">
              <el-table-column prop="name" :label="$t('employee.fileName')" min-width="240" show-overflow-tooltip />
              <el-table-column prop="file_type" :label="$t('employee.fileType')" min-width="140" align="center" />
              <el-table-column prop="uploaded_at" :label="$t('employee.uploadTime')" min-width="200" align="center">
                <template #default="{ row }">
                  {{ formatDate(row.uploaded_at) }}
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.operations')" width="220" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button type="success" size="small" @click="handleViewDocument(row)">
                      {{ $t('common.view') }}
                    </el-button>
                    <el-button type="primary" size="small" @click="handleDownloadDocument(row)">
                      {{ $t('common.download') }}
                    </el-button>
                    <el-button type="danger" size="small" @click="handleDeleteDocument(row)">
                      {{ $t('common.delete') }}
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else :description="$t('employee.noCode')" />
          </div>
        </el-tab-pane>

        <el-tab-pane name="qualifications" lazy>
          <template #label>
            <span class="tab-label-with-dot">
              <span>{{ $t('employee.qualifications') }}</span>
              <span v-if="employee?.has_qualification_update" class="tab-dot" />
            </span>
          </template>
          <div class="content-section">
            <el-tabs v-model="qualificationActiveTab" @tab-change="loadQualificationsPanel">
              <el-tab-pane :label="$t('qualifications.trainingRecords')" name="training">
                <TrainingRecordManager
                  :employee-id="employeeId"
                  :display-mode="'dropdown'"
                  :show-title="false"
                  :show-employee-select="false"
                  :show-status-columns="true"
                  :show-employee-columns="false"
                  @refresh="loadEmployee"
                />
              </el-tab-pane>
              <el-tab-pane :label="$t('qualifications.expiring')" name="expiring">
                <el-space :size="12" style="margin-bottom: 16px">
                  <span>{{ $t('qualifications.reminderDays') }}</span>
                  <el-input-number v-model="reminderDays" :min="1" :max="3650" />
                  <el-button type="primary" :loading="reminderSettingLoading" @click="saveReminderSetting">{{ $t('common.save') }}</el-button>
                </el-space>
                <el-table :data="expiringTrainingRecordsForEmployee" v-loading="qualificationsLoading" stripe table-layout="auto" style="width: 100%">
                  <el-table-column :label="$t('qualifications.trainingName')" min-width="120" show-overflow-tooltip>
                    <template #default="{ row }">
                      <span>{{ row.name || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.trainingCategory')" width="160">
                    <template #default="{ row }">
                      <span>{{ getCategoryName(row.category) || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.trainingDate')" width="160">
                    <template #default="{ row }">
                      <span>{{ formatDate(row.completed_date) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.expiryDate')" width="160">
                    <template #default="{ row }">
                      <span>{{ formatDate(row.expiry_date) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.daysUntilExpiry')" width="140">
                    <template #default="{ row }">
                      <el-tag :type="getDaysUntilExpiryTagType(row.days_until_expiry)" size="small">
                        {{ row.days_until_expiry < 0 ? $t('qualifications.expired') : `${row.days_until_expiry}${$t('qualifications.days')}` }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.reminderStatus')" width="160">
                    <template #default="{ row }">
                      <el-tag :type="getReminderStatusTag(row.reminder_status)">
                        {{ getReminderStatusText(row.reminder_status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.certificate')" width="120">
                    <template #default="{ row }">
                      <el-link v-if="row.certificate_url" type="primary" @click="openTrainingCertificatePreview(row)">{{ $t('common.view') }}</el-link>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.operations')" width="110" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
                    <template #default="{ row }">
                      <div class="action-buttons">
                        <el-button type="primary" size="small" @click="editTrainingRecord(row)">{{ $t('common.edit') }}</el-button>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!qualificationsLoading && expiringTrainingRecordsForEmployee.length === 0" :description="$t('qualifications.noExpiringRecords')" />
              </el-tab-pane>
              <el-tab-pane :label="$t('qualifications.expired')" name="expired">
                <el-table :data="expiredTrainingRecordsForEmployee" v-loading="qualificationsLoading" stripe table-layout="auto" style="width: 100%">
                  <el-table-column :label="$t('qualifications.trainingName')" min-width="120" show-overflow-tooltip>
                    <template #default="{ row }">
                      <span>{{ row.name || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.trainingCategory')" width="160">
                    <template #default="{ row }">
                      <span>{{ getCategoryName(row.category) || '-' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.trainingDate')" width="160">
                    <template #default="{ row }">
                      <span>{{ formatDate(row.completed_date) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.expiryDate')" width="160">
                    <template #default="{ row }">
                      <span>{{ formatDate(row.expiry_date) }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.daysUntilExpiry')" width="140">
                    <template #default="{ row }">
                      <el-tag :type="getDaysUntilExpiryTagType(row.days_until_expiry)" size="small">
                        {{ row.days_until_expiry < 0 ? `${$t('qualifications.expired')}${Math.abs(row.days_until_expiry)}${$t('qualifications.days')}` : `${row.days_until_expiry}${$t('qualifications.days')}` }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.reminderStatus')" width="160">
                    <template #default="{ row }">
                      <el-tag :type="getReminderStatusTag(row.reminder_status)">
                        {{ getReminderStatusText(row.reminder_status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.certificate')" width="120">
                    <template #default="{ row }">
                      <el-link v-if="row.certificate_url" type="primary" @click="openTrainingCertificatePreview(row)">{{ $t('common.view') }}</el-link>
                      <span v-else>-</span>
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('qualifications.operations')" width="110" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
                    <template #default="{ row }">
                      <div class="action-buttons">
                        <el-button type="primary" size="small" @click="editTrainingRecord(row)">{{ $t('common.edit') }}</el-button>
                      </div>
                    </template>
                  </el-table-column>
                </el-table>
                <el-empty v-if="!qualificationsLoading && expiredTrainingRecordsForEmployee.length === 0" :description="$t('qualifications.noExpiredRecords')" />
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-tab-pane>

        <el-tab-pane :label="$t('employee.onboarding')" name="onboarding" lazy>
          <div class="content-section">
            <div class="section-header section-header--right">
              <el-button type="primary" @click="handleUploadDocument">
                <el-icon><Upload /></el-icon>
                {{ $t('employee.uploadOnboarding') }}
              </el-button>
            </div>
            <el-table :data="onboardingDocuments" stripe v-if="onboardingDocuments.length > 0" style="width: 100%; margin-top: 0" table-layout="auto">
              <el-table-column prop="name" :label="$t('employee.fileName')" min-width="160" show-overflow-tooltip />
              <el-table-column prop="file_type" :label="$t('employee.fileType')" width="120" align="center" />
              <el-table-column prop="uploaded_at" :label="$t('employee.uploadTime')" width="180" align="center">
                <template #default="{ row }">
                  {{ formatDate(row.uploaded_at) }}
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.operations')" width="200" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button type="success" size="small" @click="handleViewDocument(row)">
                      {{ $t('common.view') }}
                    </el-button>
                    <el-button type="primary" size="small" @click="handleDownloadDocument(row)">
                      {{ $t('common.download') }}
                    </el-button>
                    <el-button type="danger" size="small" @click="handleDeleteDocument(row)">
                      {{ $t('common.delete') }}
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else :description="$t('employee.noOnboarding')" />
          </div>
        </el-tab-pane>

        <el-tab-pane :label="$t('employee.handbook')" name="handbook" lazy>
          <div class="content-section">
            <div class="section-header section-header--right">
              <el-button type="primary" @click="handleUploadHandbook">
                <el-icon><Upload /></el-icon>
                {{ $t('employee.uploadHandbook') }}
              </el-button>
            </div>
            <el-table :data="handbookDocuments" stripe v-if="handbookDocuments.length > 0" style="width: 100%; margin-top: 0" table-layout="auto">
              <el-table-column prop="name" :label="$t('employee.fileName')" min-width="160" show-overflow-tooltip />
              <el-table-column prop="file_type" :label="$t('employee.fileType')" width="120" align="center" />
              <el-table-column prop="uploaded_at" :label="$t('employee.uploadTime')" width="180" align="center">
                <template #default="{ row }">
                  {{ formatDate(row.uploaded_at) }}
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.operations')" width="200" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
                <template #default="{ row }">
                  <div class="action-buttons">
                    <el-button type="success" size="small" @click="handleViewDocument(row)">
                      {{ $t('common.view') }}
                    </el-button>
                    <el-button type="primary" size="small" @click="handleDownloadDocument(row)">
                      {{ $t('common.download') }}
                    </el-button>
                    <el-button type="danger" size="small" @click="handleDeleteDocument(row)">
                      {{ $t('common.delete') }}
                    </el-button>
                  </div>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else :description="$t('employee.noHandbook')" />
          </div>
        </el-tab-pane>

        <el-tab-pane :label="$t('employee.tasks')" name="tasks" lazy>
          <div class="content-section">
            <div class="filter-bar">
              <el-select v-model="filterStatus" :placeholder="$t('employee.filterStatus')" clearable style="width: 180px" @change="loadEmployeeTasks">
                <el-option :label="$t('employee.taskStatus.inProgress')" value="in_progress" />
                <el-option :label="$t('employee.taskStatus.completed')" value="completed" />
                <el-option :label="$t('employee.taskStatus.rejected')" value="rejected" />
                <el-option :label="$t('employee.taskStatus.approved')" value="approved" />
              </el-select>
            </div>
            <el-table :data="employeeTasks" v-loading="tasksLoading" stripe style="width: 100%; margin-top: 0" table-layout="auto">
              <el-table-column prop="title" :label="$t('employee.taskName')" min-width="180" show-overflow-tooltip />
              <el-table-column :label="$t('employee.customer')" min-width="160" show-overflow-tooltip>
                <template #default="{ row }">
                  {{ row.customer?.name || '-' }}
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.serviceStartTime')" min-width="240">
                <template #default="{ row }">
                  <span>{{ formatDateTimeToMinute(row.service_start_time || row.service_time) }}</span>
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.serviceEndTime')" min-width="240">
                <template #default="{ row }">
                  <span>{{ formatDateTimeToMinute(row.service_end_time) }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="status" :label="$t('employee.status')" min-width="160" align="center">
                <template #default="{ row }">
                  <el-tag :type="getTaskStatusType(row.status)" size="small">{{ getTaskStatusText(row.status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column :label="$t('employee.operations')" width="110" :fixed="isMobile ? false : 'right'" align="right" header-align="left" class-name="op-col" label-class-name="op-col-header">
                <template #default="{ row }">
                  <el-button type="primary" plain size="small" @click="handleViewTask(row)">{{ $t('common.view') }}</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!tasksLoading && employeeTasks.length === 0" :description="$t('employee.noTasks')" style="padding: 40px 0" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <!-- 上传资料对话框 -->
    <el-dialog v-model="showUploadDialog" :title="getUploadDialogTitle()" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="(file, files) => { fileList = files }"
        :file-list="fileList"
        :limit="1"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text" v-html="$t('employee.uploadDialog.dragTip')">
        </div>
        <template #tip>
          <div class="el-upload__tip">
            {{ $t('employee.uploadDialog.fileTip') }}
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showUploadDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleConfirmUpload">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- 生成合同表单对话框 -->
    <el-dialog v-model="showContractForm" :title="$t('employee.generateContract')" width="600px">
      <el-form :model="contractForm" :rules="contractFormRules" ref="contractFormRef" label-width="150px">
        <el-form-item :label="$t('employee.contractForm.startDate')" prop="start_date">
          <el-date-picker
            v-model="contractForm.start_date"
            type="date"
            :placeholder="$t('employee.contractForm.selectStartDate')"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.employmentType')" prop="employment_type">
          <el-select v-model="contractForm.employment_type" :placeholder="$t('employee.contractForm.selectEmploymentType')" style="width: 100%">
            <el-option :label="$t('employee.contractForm.employmentTypes.fullTime')" value="full-time" />
            <el-option :label="$t('employee.contractForm.employmentTypes.partTime')" value="part-time" />
            <el-option :label="$t('employee.contractForm.employmentTypes.casual')" value="casual" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.position')" prop="position">
          <el-select v-model="contractForm.position" :placeholder="$t('employee.contractForm.selectPosition')" style="width: 100%">
            <el-option :label="$t('employee.contractForm.positions.supportWorker')" value="support-worker" />
            <el-option :label="$t('employee.contractForm.positions.admin')" value="admin" />
            <el-option :label="$t('employee.contractForm.positions.officeStaff')" value="office-staff" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.superiorFirstName')" prop="superior_first_name">
          <el-input v-model="contractForm.superior_first_name" :placeholder="$t('employee.contractForm.inputSuperiorFirstName')" />
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.superiorLastName')" prop="superior_last_name">
          <el-input v-model="contractForm.superior_last_name" :placeholder="$t('employee.contractForm.inputSuperiorLastName')" />
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.superiorTitle')" prop="superior_title">
          <el-input v-model="contractForm.superior_title" :placeholder="$t('employee.contractForm.inputSuperiorTitle')" />
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.hoursPerWeek')" prop="hours_per_week">
          <el-input-number
            v-model="contractForm.hours_per_week"
            :min="0"
            :max="168"
            :placeholder="$t('employee.contractForm.inputHoursPerWeek')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.workHours')" prop="work_hours">
          <el-time-picker
            v-model="contractForm.work_hours"
            is-range
            :range-separator="$t('common.to')"
            :start-placeholder="$t('employee.contractForm.startTime')"
            :end-placeholder="$t('employee.contractForm.endTime')"
            format="HH:mm"
            value-format="HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.grossSalary')" prop="gross_salary">
          <el-input-number
            v-model="contractForm.gross_salary"
            :min="0"
            :precision="2"
            :placeholder="$t('employee.contractForm.inputGrossSalary')"
            style="width: 100%"
          >
            <template #prepend>$</template>
          </el-input-number>
        </el-form-item>
        <el-form-item :label="$t('employee.contractForm.signatureDate')" prop="signature_date">
          <el-date-picker
            v-model="contractForm.signature_date"
            type="date"
            :placeholder="$t('employee.contractForm.selectSignatureDate')"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showContractForm = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="contractGenerating" @click="handleGenerateContract">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 预览对话框 -->
    <el-dialog v-model="showPreviewDialog" :title="currentPreviewDocument?.name || $t('employee.preview.title')" width="90%" top="5vh" @close="handleClosePreview">
      <div class="preview-wrapper" ref="previewWrapper">
        <!-- Word文档预览 -->
        <div 
          v-if="previewType === 'docx'" 
          ref="docxPreviewContainer" 
          class="preview-docx"
        ></div>
        <div
          v-else-if="previewType === 'pdfjs'"
          ref="previewPdfContainer"
          class="preview-pdfjs"
        >
          <div ref="previewPdfCanvasWrapper" class="preview-pdfjs-canvases"></div>
        </div>
        <!-- PDF和图片预览 -->
        <iframe 
          v-else-if="previewUrl && previewType === 'blob'" 
          :src="previewUrl" 
          class="preview-iframe"
        ></iframe>
        <!-- 不支持预览的格式 -->
        <div v-else-if="previewType === 'unsupported'" class="preview-unsupported">
          <el-icon style="font-size: 64px; color: #909399; margin-bottom: 20px;"><Document /></el-icon>
          <p style="color: #606266; font-size: 16px; margin-bottom: 10px;">{{ $t('employee.preview.unsupported') }}</p>
          <p style="color: #909399; font-size: 14px;">{{ $t('employee.preview.downloadTip') }}</p>
        </div>
        <!-- 加载中 -->
        <div v-else class="preview-loading">
          <el-space>
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>{{ $t('employee.preview.loading') }}</span>
          </el-space>
        </div>
      </div>
      <template #footer>
        <el-button @click="showPreviewDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleDownloadDocument(currentPreviewDocument)" v-if="currentPreviewDocument">
          {{ $t('common.download') }}
        </el-button>
      </template>
    </el-dialog>
    
    <el-dialog v-model="previewQualificationDialogVisible" :title="$t('employee.viewCertificate')" width="900px" @closed="clearQualificationPreview">
      <div class="preview-wrapper" v-loading="previewQualificationLoading">
        <div v-if="previewQualificationLoading" class="preview-loading">{{ $t('employee.preview.loading') }}</div>
        <iframe
          v-else-if="qualificationPreviewUrl && isQualificationPreviewPdf(qualificationPreviewUrl, qualificationPreviewMime)"
          :src="qualificationPreviewUrl"
          class="preview-iframe"
        ></iframe>
        <img
          v-else-if="qualificationPreviewUrl"
          :src="qualificationPreviewUrl"
          :alt="$t('employee.viewCertificate')"
          class="preview-image"
        />
        <div v-else class="preview-loading">{{ $t('qualifications.noCertificate') }}</div>
      </div>
      <template #footer>
        <el-button @click="previewQualificationDialogVisible = false">{{ $t('common.cancel') }}</el-button>
      </template>
    </el-dialog>

    <!-- 合同签字流程对话框（4步流程） -->
    <el-dialog v-model="showContractSignatureFlowDialog" :title="$t('employee.contractSignatureTitle')" width="90%" top="5vh" @close="handleCloseSignatureFlowDialog">
      <!-- 步骤指示器 -->
      <div class="signature-flow-steps">
        <div class="step-item" :class="{ active: signatureFlowStep >= 0, completed: signatureFlowStep > 0 }">
          <div class="step-number">1</div>
          <div class="step-label">{{ $t('employee.stepSelectPosition') }}</div>
        </div>
        <div class="step-connector" :class="{ completed: signatureFlowStep > 0 }"></div>
        <div class="step-item" :class="{ active: signatureFlowStep >= 1, completed: signatureFlowStep > 1 }">
          <div class="step-number">2</div>
          <div class="step-label">{{ $t('employee.stepSign') }}</div>
        </div>
        <div class="step-connector" :class="{ completed: signatureFlowStep > 1 }"></div>
        <div class="step-item" :class="{ active: signatureFlowStep >= 2, completed: signatureFlowStep > 2 }">
          <div class="step-number">3</div>
          <div class="step-label">{{ $t('employee.stepPreview') }}</div>
        </div>
      </div>

      <!-- 步骤内容 -->
      <div class="signature-flow-content">
        <!-- 步骤1: 选择坐标 -->
        <div v-if="signatureFlowStep === 0" class="step-content">
          <div style="margin-bottom: 10px; color: #909399; font-size: 14px;">
            {{ $t('employee.contractSignatureInstruction') }}
          </div>
          <div v-if="isMobile" class="signature-position-toolbar">
            <div class="signature-position-toolbar-left">
              <el-button
                size="small"
                :type="positionSelectionMode === 'select' ? 'primary' : 'default'"
                @click="setPositionSelectionMode('select')"
              >
                {{ $t('employee.positionSelectMode') }}
              </el-button>
              <el-button
                size="small"
                :type="positionSelectionMode === 'scroll' ? 'primary' : 'default'"
                @click="setPositionSelectionMode('scroll')"
              >
                {{ $t('employee.positionScrollMode') }}
              </el-button>
            </div>
            <div class="signature-position-toolbar-right">
              <el-button size="small" :disabled="positionPdfZoom <= 1" @click="decreasePositionPdfZoom">-</el-button>
              <div class="zoom-text">{{ Math.round(positionPdfZoom * 100) }}%</div>
              <el-button size="small" :disabled="positionPdfZoom >= 2.5" @click="increasePositionPdfZoom">+</el-button>
            </div>
          </div>
          <div
            ref="signaturePositionContainer"
            class="signature-position-container"
            :class="{
              selecting: isSelectingPosition,
              'select-mode': positionSelectionMode === 'select',
              'scroll-mode': positionSelectionMode === 'scroll'
            }"
            @scroll="handlePositionScroll"
            @pointerdown="handlePositionPointerDown"
            @pointermove="handlePositionPointerMove"
            @pointerup="handlePositionPointerUp"
            @pointercancel="handlePositionPointerUp"
            @touchstart="handlePositionTouchStart"
            @touchmove="handlePositionTouchMove"
            @touchend="handlePositionTouchEnd"
            @touchcancel="handlePositionTouchEnd"
            @wheel="handlePositionWheel"
          >
            <div
              ref="positionPdfContainer"
              class="signature-position-pdf"
            >
              <div ref="positionPdfCanvasWrapper" class="position-pdf-canvases"></div>
              <div
                v-if="positionRect && positionRect.width > 0 && positionRect.height > 0"
                class="signature-position-rect"
                :style="{
                  left: positionRect.left + 'px',
                  top: positionRect.top + 'px',
                  width: positionRect.width + 'px',
                  height: positionRect.height + 'px'
                }"
              ></div>
            </div>
          </div>
          <div v-if="positionRect" class="selected-position-info">
            <el-card>
              <div>{{ $t('employee.positionSelected') }}</div>
              <div>X: {{ positionNormalized?.x?.toFixed(3) || '0.000' }}, Y: {{ positionNormalized?.y?.toFixed(3) || '0.000' }}</div>
              <div>{{ $t('employee.width') }}: {{ positionNormalized?.width?.toFixed(3) || '0.000' }}, {{ $t('employee.height') }}: {{ positionNormalized?.height?.toFixed(3) || '0.000' }}</div>
              <el-form-item :label="$t('employee.pageNumberLabel')" class="page-number-form-item">
                <el-space>
                  <el-input-number
                    v-model="currentPageNumber"
                    :min="0"
                    :max="999"
                    @change="updatePageNumber"
                    style="width: 120px;"
                  />
                  <span class="page-hint">{{ $t('employee.pageNumberHint') }}</span>
                </el-space>
              </el-form-item>
            </el-card>
          </div>
        </div>

        <!-- 步骤2: 签字 -->
        <div v-if="signatureFlowStep === 1" class="step-content">
          <el-form :label-width="isMobile ? 'auto' : '100px'" :label-position="isMobile ? 'top' : 'right'">
            <el-form-item :label="$t('employee.signatureMethod')">
              <el-radio-group v-model="contractSignatureMethod">
                <el-radio :label="0">{{ $t('employee.signatureMethodDraw') }}</el-radio>
                <el-radio :label="1">{{ $t('employee.signatureMethodUpload') }}</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item v-if="contractSignatureMethod === 0" :label="$t('employee.signatureMethodDraw')">
              <canvas
                ref="contractSignatureCanvas"
                width="600"
                height="300"
                :style="signatureCanvasStyle"
                @pointerdown="handleCanvasPointerDown"
                @pointermove="handleCanvasPointerMove"
                @pointerup="handleCanvasPointerUp"
                @pointercancel="handleCanvasPointerUp"
                @pointerleave="handleCanvasPointerUp"
                @touchstart="handleCanvasTouchStart"
                @touchmove="handleCanvasTouchMove"
                @touchend="handleCanvasTouchEnd"
                @touchcancel="handleCanvasTouchEnd"
              ></canvas>
              <div style="margin-top: 10px;">
                <el-button size="small" @click="clearCanvas">{{ $t('employee.clear') }}</el-button>
              </div>
            </el-form-item>
            
            <el-form-item v-if="contractSignatureMethod === 1" :label="$t('employee.signatureMethodUpload')">
              <el-upload
                :auto-upload="false"
                :limit="1"
                :on-change="handleContractSignatureFileChange"
                :file-list="contractSignatureFile ? [{ name: contractSignatureFile.name, raw: contractSignatureFile }] : []"
              >
                <el-button type="primary">{{ $t('employee.chooseFile') }}</el-button>
                <template #tip>
                  <div class="el-upload__tip">{{ $t('employee.signatureFileTip') }}</div>
                </template>
              </el-upload>
            </el-form-item>
          </el-form>
        </div>

        <!-- 步骤3: 预览 -->
        <div v-if="signatureFlowStep === 2" class="step-content">
          <div class="preview-container">
            <div
              ref="signaturePreviewPdfContainer"
              class="signature-preview-pdf"
            ></div>
            <div v-if="!signaturePreviewPdfRendered" class="preview-loading">
              <el-icon class="is-loading"><Loading /></el-icon>
              <div>{{ $t('employee.previewLoading') }}</div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="handleCloseSignatureFlowDialog">{{ $t('common.cancel') }}</el-button>
        <el-button v-if="signatureFlowStep === 0" type="primary" :disabled="!positionRect" @click="handleSavePositionAndNext" :loading="savingSignaturePosition">
          {{ $t('employee.savePositionNext') }}
        </el-button>
        <el-button v-if="signatureFlowStep === 1" type="primary" @click="previewContractSignature" :loading="contractSignatureUploading">
          {{ $t('common.confirm') }}
        </el-button>
        <el-button v-if="signatureFlowStep === 2" @click="restartContractSignature" :disabled="confirmSigning">
          {{ $t('employee.redoSign') }}
        </el-button>
        <el-button v-if="signatureFlowStep === 2" type="primary" @click="confirmContractSignature" :loading="confirmSigning">
          {{ $t('employee.confirmSubmit') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 旧的合同签字坐标对话框（保留用于兼容，但不再使用） -->
    <el-dialog v-model="showContractSignaturePositionDialog" :title="$t('employee.selectSignaturePositionTitle')" width="90%" top="5vh" @close="handleCloseSignaturePositionDialog" v-if="false">
      <div
        ref="signaturePositionContainer"
        class="signature-position-container"
        @scroll="handlePositionScroll"
        @mousedown="handlePositionMouseDown"
        @mousemove="handlePositionMouseMove"
        @mouseup="handlePositionMouseUp"
        @mouseleave="handlePositionMouseUp"
      >
        <div
          v-if="positionPreviewType === 'pdf'"
          ref="positionPdfContainer"
          class="signature-position-pdf"
        ></div>
        <img
          v-else-if="positionPreviewType === 'image' && positionPreviewUrl"
          :src="positionPreviewUrl"
          class="signature-position-image"
        />
        <div
          v-else-if="positionPreviewType === 'docx'"
          ref="positionDocxContainer"
          class="signature-position-docx"
        ></div>
        <iframe
          v-else-if="positionPreviewType === 'blob' && positionPreviewUrl"
          :src="positionPreviewUrl"
          class="signature-position-iframe"
        ></iframe>
        <div v-else class="signature-position-unsupported">
          {{ $t('employee.previewUnsupportedFormat') }}
        </div>
        <div
          v-if="positionRect"
          class="signature-position-rect"
          :style="{
            left: positionRect.left + 'px',
            top: positionRect.top + 'px',
            width: positionRect.width + 'px',
            height: positionRect.height + 'px'
          }"
        ></div>
      </div>
      <template #footer>
        <el-button @click="showContractSignaturePositionDialog = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :disabled="!positionRect" @click="saveSignaturePosition" :loading="savingSignaturePosition">
          {{ $t('employee.savePosition') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="sendSignLinkLangDialogVisible" :title="$t('employee.sendContractSignLink')" width="360px">
      <el-form label-width="80px">
        <el-form-item :label="$t('common.language')">
          <el-select v-model="sendSignLinkLang" style="width: 100%">
            <el-option :label="$t('common.chinese')" value="zh" />
            <el-option :label="$t('common.english')" value="en" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendSignLinkLangDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="sendSignLinkSubmitting" @click="submitSendSignLink">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick, watch, inject, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getEmployee, getEmployeeDocuments, uploadEmployeeDocument, previewEmployeeDocument, downloadEmployeeDocument, deleteEmployeeDocument, generateEmployeeContract, createEmployeeContractSignLink, signEmployeeContract, saveEmployeeContractSignaturePosition, updateEmployeeAccountStatus, getExpiringTrainingRecords, getExpiredTrainingRecords, getTrainingRecordReminderSettings, updateTrainingRecordReminderSettings } from '@/api/employees'
import { getTasks } from '@/api/tasks'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Document, FirstAidKit, Folder, Upload, UploadFilled, Menu, CircleCheck, TrendCharts, Tickets, Loading, EditPen, Trophy } from '@element-plus/icons-vue'
import { formatDate, formatDateTimeToMinute } from '@/utils/formatters'
import TrainingRecordManager from '@/components/TrainingRecordManager.vue'
import { renderAsync } from 'docx-preview'
import * as pdfjsDistLegacy from 'pdfjs-dist/legacy/build/pdf.js'
import pdfjsDistLegacyWorkerUrl from 'pdfjs-dist/legacy/build/pdf.worker.min.js?url'
import api from '@/api'
import { markUpdatesRead } from '@/api/updates'

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

const getAxiosErrorDetail = async (error) => {
  const data = error?.response?.data
  if (data instanceof Blob) {
    try {
      const text = await data.text()
      try {
        const json = JSON.parse(text)
        return json?.detail || json?.message || text
      } catch {
        return text
      }
    } catch {
      return error?.message || t('common.noData')
    }
  }
  return error?.response?.data?.detail || error?.message || t('common.noData')
}

const route = useRoute()
const router = useRouter()
const employeeId = route.params.id
const employee = ref({})
const accountStatusDraft = ref('normal')
const loading = ref(false)
const initialTab = route.query.tab
const normalizedInitialTab = initialTab === 'training' ? 'qualifications' : initialTab
const allowedTabs = ['contract', 'code', 'qualifications', 'onboarding', 'tasks', 'handbook']
const activeMenu = ref(allowedTabs.includes(normalizedInitialTab) ? normalizedInitialTab : 'contract')
const showUploadDialog = ref(false)
const uploadRef = ref(null)
const fileList = ref([])
const currentUploadType = ref('')

// 预览相关
const showPreviewDialog = ref(false)
const previewUrl = ref('')
const currentPreviewDocument = ref(null)
const previewType = ref('') // 'blob', 'docx', 'pdfjs', 'unsupported'
const docxPreviewContainer = ref(null)
const previewWrapper = ref(null)
const previewPdfContainer = ref(null)
const previewPdfCanvasWrapper = ref(null)
const previewBlob = ref(null)
const previewPdfRenderedKey = ref('')

// 文档列表（示例数据，实际应从后端获取）
const contractDocuments = ref([])
const codeDocuments = ref([])
const onboardingDocuments = ref([])
const handbookDocuments = ref([])

// 任务相关
const employeeTasks = ref([])
const tasksLoading = ref(false)
const filterStatus = ref('')

// 合同生成相关
const showContractForm = ref(false)
const contractFormRef = ref(null)
const contractGenerating = ref(false)
const sendSignLinkLangDialogVisible = ref(false)
const sendSignLinkLang = ref('en')
const sendSignLinkSubmitting = ref(false)
const pendingSignLinkContractId = ref('')

// 合同签字流程相关（4步流程）
const showContractSignatureFlowDialog = ref(false)
const signatureFlowStep = ref(0) // 0: 选择坐标, 1: 签字, 2: 预览
const currentContractForSign = ref(null)
const contractSignatureCanvas = ref(null)
const contractSignatureMethod = ref(0) // 0: 手写签名, 1: 上传图片
const contractSignatureFile = ref(null)
const contractSignatureUploading = ref(false)
const contractSignatureSubmitted = ref(false)
const confirmSigning = ref(false)
const draftSignatureDataUrl = ref('')
const draftSignatureDate = ref('')
const draftSignatureSubmitDataUrl = ref('')
const isDrawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)
const signaturePreviewUrl = ref('')
const signaturePreviewPdfContainer = ref(null)
const signaturePreviewPdfRendered = ref(false)

// 合同签字坐标相关
const signaturePositionContainer = ref(null)
const positionPdfContainer = ref(null)
const positionPdfCanvasWrapper = ref(null)
const positionPreviewUrl = ref('')
const positionRect = ref(null)
const positionNormalized = ref(null)
const currentPageNumber = ref(0)
const pdfContentSize = ref({ width: 0, height: 0 })
const positionStart = ref({ x: 0, y: 0 })
const isSelectingPosition = ref(false)
const positionSelectionMode = ref('select')
const positionPdfZoom = ref(isMobile.value ? 1.8 : 1)
const positionSelectingPointerId = ref(null)
const positionPdfSourceBlob = ref(null)
const positionPdfDoc = shallowRef(null)
const positionPdfBytes = ref(null)
const savingSignaturePosition = ref(false)

// 旧的对话框（保留用于兼容，但不再使用）
const showContractSignatureDialog = ref(false)
const showContractSignaturePositionDialog = ref(false)
const currentContractForPosition = ref(null)

const handleCanvasMouseDown = (e) => {
  isDrawing.value = true
  const canvas = contractSignatureCanvas.value
  const rect = canvas.getBoundingClientRect()
  lastX.value = e.clientX - rect.left
  lastY.value = e.clientY - rect.top
}

const handleCanvasMouseMove = (e) => {
  if (!isDrawing.value) return
  const canvas = contractSignatureCanvas.value
  const ctx = canvas.getContext('2d')
  const rect = canvas.getBoundingClientRect()
  const currentX = e.clientX - rect.left
  const currentY = e.clientY - rect.top
  
  ctx.strokeStyle = '#000000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.moveTo(lastX.value, lastY.value)
  ctx.lineTo(currentX, currentY)
  ctx.stroke()
  
  lastX.value = currentX
  lastY.value = currentY
}

const handleCanvasMouseUp = () => {
  isDrawing.value = false
}

const getCanvasPoint = (clientX, clientY) => {
  const canvas = contractSignatureCanvas.value
  const rect = canvas.getBoundingClientRect()
  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  const clamp = (v, min, max) => Math.max(min, Math.min(v, max))
  return {
    x: clamp((clientX - rect.left) * scaleX, 0, canvas.width),
    y: clamp((clientY - rect.top) * scaleY, 0, canvas.height)
  }
}

const signatureCanvasStyle = computed(() => ({
  border: '1px solid #ddd',
  cursor: 'crosshair',
  touchAction: 'none',
  width: '100%',
  maxWidth: '100%',
  height: isMobile.value ? '220px' : '300px'
}))

const handleCanvasPointerDown = (event) => {
  if (contractSignatureMethod.value !== 0) return
  if (!contractSignatureCanvas.value) return
  if (event.pointerType === 'mouse' && event.button !== 0) return
  event.preventDefault()
  event.stopPropagation()
  try {
    contractSignatureCanvas.value.setPointerCapture?.(event.pointerId)
  } catch {}
  isDrawing.value = true
  const p = getCanvasPoint(event.clientX, event.clientY)
  lastX.value = p.x
  lastY.value = p.y
}

const handleCanvasPointerMove = (event) => {
  if (!isDrawing.value) return
  if (!contractSignatureCanvas.value) return
  event.preventDefault()
  event.stopPropagation()
  const canvas = contractSignatureCanvas.value
  const ctx = canvas.getContext('2d')
  const p = getCanvasPoint(event.clientX, event.clientY)
  ctx.strokeStyle = '#000000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.moveTo(lastX.value, lastY.value)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
  lastX.value = p.x
  lastY.value = p.y
}

const handleCanvasPointerUp = (event) => {
  if (!isDrawing.value) return
  isDrawing.value = false
  try {
    contractSignatureCanvas.value?.releasePointerCapture?.(event.pointerId)
  } catch {}
}

const getFirstTouch = (touchEvent) => {
  const t = touchEvent?.touches?.[0] || touchEvent?.changedTouches?.[0]
  if (!t) return null
  return t
}

const handleCanvasTouchStart = (event) => {
  if (contractSignatureMethod.value !== 0) return
  const t = getFirstTouch(event)
  if (!t) return
  event.preventDefault()
  event.stopPropagation()
  isDrawing.value = true
  const p = getCanvasPoint(t.clientX, t.clientY)
  lastX.value = p.x
  lastY.value = p.y
}

const handleCanvasTouchMove = (event) => {
  if (!isDrawing.value) return
  const t = getFirstTouch(event)
  if (!t) return
  event.preventDefault()
  event.stopPropagation()
  const canvas = contractSignatureCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const p = getCanvasPoint(t.clientX, t.clientY)
  ctx.strokeStyle = '#000000'
  ctx.lineWidth = 2
  ctx.lineCap = 'round'
  ctx.beginPath()
  ctx.moveTo(lastX.value, lastY.value)
  ctx.lineTo(p.x, p.y)
  ctx.stroke()
  lastX.value = p.x
  lastY.value = p.y
}

const handleCanvasTouchEnd = (event) => {
  if (!isDrawing.value) return
  event.preventDefault()
  event.stopPropagation()
  isDrawing.value = false
}

const clearCanvas = () => {
  const canvas = contractSignatureCanvas.value
  if (canvas) {
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }
}
const contractForm = reactive({
  start_date: '',
  employment_type: '',
  position: '',
  superior_first_name: '',
  superior_last_name: '',
  superior_title: '',
  hours_per_week: null,
  work_hours: null,
  gross_salary: null,
  signature_date: ''
})

const contractFormRules = computed(() => ({
  start_date: [{ required: true, message: t('employee.contractForm.selectStartDate'), trigger: 'change' }],
  employment_type: [{ required: true, message: t('employee.contractForm.selectEmploymentType'), trigger: 'change' }],
  position: [{ required: true, message: t('employee.contractForm.selectPosition'), trigger: 'change' }],
  superior_first_name: [{ required: true, message: t('employee.contractForm.inputSuperiorFirstName'), trigger: 'blur' }],
  superior_last_name: [{ required: true, message: t('employee.contractForm.inputSuperiorLastName'), trigger: 'blur' }],
  superior_title: [{ required: true, message: t('employee.contractForm.inputSuperiorTitle'), trigger: 'blur' }],
  hours_per_week: [{ required: true, message: t('employee.contractForm.inputHoursPerWeek'), trigger: 'blur' }],
  work_hours: [{ required: true, message: t('employee.contractForm.workHours'), trigger: 'change' }],
  gross_salary: [{ required: true, message: t('employee.contractForm.inputGrossSalary'), trigger: 'blur' }],
  signature_date: [{ required: true, message: t('employee.contractForm.selectSignatureDate'), trigger: 'change' }]
}))

const normalizeAccountStatus = (value) => {
  const normalized = String(value || 'normal').trim().toLowerCase()
  return normalized === 'disabled' ? 'disabled' : 'normal'
}

const getAccountStatusText = (value) => {
  const normalized = normalizeAccountStatus(value)
  return normalized === 'disabled'
    ? t('employee.accountStatusDisabled')
    : t('employee.accountStatusNormal')
}

const handleAccountStatusChange = async (nextValue) => {
  const previous = normalizeAccountStatus(employee.value?.account_status)
  const next = normalizeAccountStatus(nextValue)
  if (next === previous) return

  try {
    await ElMessageBox.confirm(
      t('employee.accountStatusChangeConfirm', { status: getAccountStatusText(next) }),
      t('common.confirm'),
      { type: 'warning' }
    )
  } catch {
    accountStatusDraft.value = previous
    return
  }

  try {
    await updateEmployeeAccountStatus(employeeId, next)
    employee.value = { ...(employee.value || {}), account_status: next }
    accountStatusDraft.value = next
    ElMessage.success(t('employee.accountStatusUpdated'))
  } catch (error) {
    accountStatusDraft.value = previous
    ElMessage.error(t('common.operationFailed'))
  }
}


const loadEmployee = async () => {
  loading.value = true
  try {
    employee.value = await getEmployee(employeeId)
    accountStatusDraft.value = normalizeAccountStatus(employee.value?.account_status)
    // TODO: 加载操作记录和入职资料
    // loadOperationRecords()
    // loadOnboardingDocuments()
  } catch (error) {
    ElMessage.error(t('employee.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleTabChange = (key) => {
  if (!key) return
  activeMenu.value = key
  if (route.query.tab !== key) {
    router.replace({ query: { ...route.query, tab: key } })
  }
  if (key === 'tasks') {
    loadEmployeeTasks()
  } else if (key === 'qualifications') {
    loadReminderSetting()
    loadQualificationsPanel()
    markQualificationReadIfNeeded()
  } else if (['contract', 'code', 'onboarding', 'handbook'].includes(key)) {
    loadDocuments(key)
  }
}

// 上传相关方法
const handleUploadContract = () => {
  currentUploadType.value = 'contract'
  showUploadDialog.value = true
  fileList.value = []
}

const handleUploadCode = () => {
  currentUploadType.value = 'code'
  showUploadDialog.value = true
  fileList.value = []
}

const handleUploadDocument = () => {
  currentUploadType.value = 'onboarding'
  showUploadDialog.value = true
  fileList.value = []
}

const handleUploadHandbook = () => {
  currentUploadType.value = 'handbook'
  showUploadDialog.value = true
  fileList.value = []
}

const handleConfirmUpload = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning(t('employee.messages.selectFile'))
    return
  }
  
  const file = fileList.value[0].raw || fileList.value[0]
  if (!file) {
    ElMessage.warning(t('employee.messages.selectFile'))
    return
  }
  
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('document_type', currentUploadType.value)
    
    await uploadEmployeeDocument(employeeId, currentUploadType.value, formData)
    ElMessage.success(t('employee.messages.uploadSuccess'))
    showUploadDialog.value = false
    fileList.value = []
    currentUploadType.value = ''
    // 重新加载对应的文档列表
    loadDocuments(activeMenu.value)
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error(t('employee.messages.uploadFailed') + ': ' + (error.response?.data?.detail || error.message || t('common.noData')))
  }
}

// 加载文档列表
const loadDocuments = async (documentType) => {
  try {
    const documents = await getEmployeeDocuments(employeeId, documentType)
    const typeMap = {
      'contract': contractDocuments,
      'code': codeDocuments,
      'onboarding': onboardingDocuments,
      'handbook': handbookDocuments
    }
    if (typeMap[documentType]) {
      typeMap[documentType].value = documents
    }
  } catch (error) {
    console.error('加载文档列表失败:', error)
    ElMessage.error(t('employee.messages.loadDocumentsFailed'))
  }
}

const buildFullSignUrl = (signUrl) => {
  if (!signUrl) return ''
  if (/^https?:\/\//i.test(signUrl)) return signUrl
  const normalized = signUrl.startsWith('/') ? signUrl : `/${signUrl}`
  const appBase = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  if (appBase && normalized.startsWith(`${appBase}/`)) {
    return `${window.location.origin}${normalized}`
  }
  return `${window.location.origin}${appBase}${normalized}`
}

const copyToClipboard = async (text) => {
  if (!text) return false
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
  } catch {
  }
  try {
    const ta = document.createElement('textarea')
    ta.value = text
    ta.setAttribute('readonly', 'true')
    ta.style.position = 'fixed'
    ta.style.left = '-9999px'
    ta.style.top = '-9999px'
    document.body.appendChild(ta)
    ta.select()
    const ok = document.execCommand('copy')
    document.body.removeChild(ta)
    return ok
  } catch {
    return false
  }
}

const qualificationActiveTab = ref(route.query.qualificationTab || 'training')
const qualificationsLoading = ref(false)
const expiringTrainingRecords = ref([])
const expiredTrainingRecords = ref([])
const reminderDays = ref(90)
const reminderSettingLoading = ref(false)

const getRowEmployeeId = (row) => {
  return row?.employee_id ?? row?.employee?.id ?? row?.employeeId ?? null
}

const expiringTrainingRecordsForEmployee = computed(() => {
  return expiringTrainingRecords.value.filter((r) => String(getRowEmployeeId(r)) === String(employeeId))
})

const expiredTrainingRecordsForEmployee = computed(() => {
  return expiredTrainingRecords.value.filter((r) => String(getRowEmployeeId(r)) === String(employeeId))
})

const previewQualificationDialogVisible = ref(false)
const qualificationPreviewUrl = ref('')
const qualificationPreviewMime = ref('')
const previewQualificationLoading = ref(false)

const isQualificationPreviewPdf = (url, mime) => {
  const m = (mime || '').toLowerCase()
  if (m.includes('application/pdf') || m.includes('pdf')) return true
  const u = (url || '').toLowerCase()
  return u.includes('.pdf')
}

const clearQualificationPreview = () => {
  if (qualificationPreviewUrl.value) {
    URL.revokeObjectURL(qualificationPreviewUrl.value)
  }
  qualificationPreviewUrl.value = ''
  qualificationPreviewMime.value = ''
  previewQualificationLoading.value = false
}

const loadReminderSetting = async () => {
  try {
    const result = await getTrainingRecordReminderSettings()
    if (result?.days) {
      reminderDays.value = result.days
    }
  } catch {
    ElMessage.error(t('qualifications.messages.loadReminderFailed'))
  }
}

const saveReminderSetting = async () => {
  if (!reminderDays.value || reminderDays.value <= 0) {
    ElMessage.error(t('qualifications.messages.reminderDaysRequired'))
    return
  }
  reminderSettingLoading.value = true
  try {
    await updateTrainingRecordReminderSettings(reminderDays.value)
    ElMessage.success(t('qualifications.messages.saveSuccess'))
    if (qualificationActiveTab.value === 'expiring') {
      await loadQualificationsPanel()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('qualifications.messages.saveFailed'))
  } finally {
    reminderSettingLoading.value = false
  }
}

const getCategoryName = (category) => {
  const categoryMap = {
    'first-aid': 'First Aid',
    'manual-handling': 'Manual Handling',
    'certificate': 'Certificate'
  }
  return categoryMap[category] || category
}

const getReminderStatusText = (status) => {
  const statusMap = {
    '3_months': t('qualifications.reminderStatusText.threeMonths'),
    '1_month': t('qualifications.reminderStatusText.oneMonth'),
    '1_week': t('qualifications.reminderStatusText.oneWeek'),
    'expired': t('qualifications.reminderStatusText.expired'),
    'normal': t('qualifications.reminderStatusText.normal')
  }
  return statusMap[status] || status
}

const getReminderStatusTag = (status) => {
  const tagMap = {
    '3_months': 'warning',
    '1_month': 'warning',
    '1_week': 'danger',
    'expired': 'danger',
    'normal': 'info'
  }
  return tagMap[status] || 'info'
}

const getDaysUntilExpiryTagType = (days) => {
  if (days < 0) return 'danger'
  if (days <= 7) return 'warning'
  if (days <= 30) return 'warning'
  return 'success'
}

const openTrainingCertificatePreview = async (row) => {
  previewQualificationDialogVisible.value = true
  clearQualificationPreview()
  previewQualificationLoading.value = true

  const baseUrl = (api?.defaults?.baseURL || '').replace(/\/$/, '')
  const targetEmployeeId = getRowEmployeeId(row) || employeeId

  try {
    const token = localStorage.getItem('token')
    const fetchBlob = async (url) => {
      const response = await fetch(url, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        cache: 'no-store'
      })
      const contentType = (response.headers.get('content-type') || '').toLowerCase()
      if (contentType.includes('application/json') || contentType.includes('text/html')) {
        let detail = ''
        try {
          const text = await response.text()
          try {
            const json = JSON.parse(text)
            detail = json?.detail || json?.message || text
          } catch {
            detail = text
          }
        } catch {
          detail = `${response.status} ${response.statusText}`
        }
        throw new Error(detail || `${response.status} ${response.statusText}`)
      }

      if (!response.ok) {
        let detail = ''
        try {
          const text = await response.text()
          try {
            const json = JSON.parse(text)
            detail = json?.detail || json?.message || text
          } catch {
            detail = text
          }
        } catch {
          detail = `${response.status} ${response.statusText}`
        }
        throw new Error(detail || `${response.status} ${response.statusText}`)
      }
      const blob = await response.blob()
      return { blob, contentType: blob.type || response.headers.get('content-type') || '' }
    }

    const apiEndpoint = `${baseUrl}/houtai/employees/${targetEmployeeId}/training-records/${row.id}/certificate`
    const requestUrl = `${apiEndpoint}?_t=${Date.now()}`
    const { blob, contentType } = await fetchBlob(requestUrl)
    qualificationPreviewMime.value = contentType
    qualificationPreviewUrl.value = URL.createObjectURL(blob)
  } catch (e) {
    ElMessage.error((e?.message && String(e.message).trim()) ? e.message : t('qualifications.messages.certificateLoadFailed'))
  } finally {
    previewQualificationLoading.value = false
  }
}

const editTrainingRecord = (row) => {
  qualificationActiveTab.value = 'training'
  router.replace({
    query: {
      ...route.query,
      tab: 'qualifications',
      qualificationTab: 'training',
      recordId: row?.id
    }
  })
}

const loadQualificationsPanel = async () => {
  qualificationsLoading.value = true
  try {
    if (qualificationActiveTab.value === 'expiring') {
      const result = await getExpiringTrainingRecords(reminderDays.value)
      expiringTrainingRecords.value = result || []
    } else if (qualificationActiveTab.value === 'expired') {
      const result = await getExpiredTrainingRecords()
      expiredTrainingRecords.value = result || []
    } else if (qualificationActiveTab.value === 'training') {
    }
  } catch {
    ElMessage.error(t('qualifications.messages.loadFailed'))
  } finally {
    qualificationsLoading.value = false
  }
}

const qualificationUnreadMarked = ref(false)
const markQualificationReadIfNeeded = async () => {
  if (qualificationUnreadMarked.value) return
  if (!employee.value?.has_qualification_update) return
  qualificationUnreadMarked.value = true
  try {
    await markUpdatesRead('employee_qualification', employeeId)
    employee.value = { ...(employee.value || {}), has_qualification_update: false }
    try {
      window.dispatchEvent(new Event('updates-changed'))
    } catch {}
  } catch {}
}

watch(
  () => ({ tab: activeMenu.value, has: employee.value?.has_qualification_update }),
  (v) => {
    if (v?.tab === 'qualifications') {
      markQualificationReadIfNeeded()
    }
  },
  { immediate: true }
)

const sendContractSignLink = async (contractId, { copy = true, language = null } = {}) => {
  const email = employee.value?.email
  if (!email) {
    ElMessage.error(t('employee.messages.cannotSendContractSignLink'))
    return null
  }
  try {
    const res = await createEmployeeContractSignLink(employeeId, contractId, language)
    const fullUrl = buildFullSignUrl(res?.sign_url)
    if (copy && fullUrl) {
      await copyToClipboard(fullUrl)
    }
    ElMessage.success(t('employee.messages.contractSignLinkSentSuccess') + email)
    return { ...res, full_url: fullUrl }
  } catch (error) {
    const detail = await getAxiosErrorDetail(error)
    ElMessage.error(t('employee.messages.contractSignLinkSentFailed') + ': ' + detail)
    return null
  }
}

const handleSendContractSignLink = async (row) => {
  if (!row?.id) return
  pendingSignLinkContractId.value = row.id
  sendSignLinkLang.value = 'en'
  sendSignLinkLangDialogVisible.value = true
}

const submitSendSignLink = async () => {
  if (!pendingSignLinkContractId.value) return
  sendSignLinkSubmitting.value = true
  try {
    await sendContractSignLink(pendingSignLinkContractId.value, { copy: true, language: sendSignLinkLang.value })
    sendSignLinkLangDialogVisible.value = false
  } finally {
    sendSignLinkSubmitting.value = false
  }
}

const renderPdfInPreviewDialog = async (blob) => {
  if (!previewPdfContainer.value || !previewPdfCanvasWrapper.value) return
  const canvasWrapper = previewPdfCanvasWrapper.value
  const key = `${currentPreviewDocument.value?.id || ''}@@${blob?.size || 0}@@${blob?.type || ''}`
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

const handleViewDocument = async (row) => {
  try {
    if (previewType.value === 'blob' && previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
    }
    if (previewPdfCanvasWrapper.value) {
      previewPdfCanvasWrapper.value.innerHTML = ''
    }
    previewPdfRenderedKey.value = ''
    previewBlob.value = null
    currentPreviewDocument.value = row
    const fileName = (row.name || '').toLowerCase()
    const fileType = (row.file_type || '').toLowerCase()
    const fileUrl = (row.file_url || '').toLowerCase()

    const getExtension = () => {
      if (fileType) {
        if (fileType.startsWith('.')) return fileType
        if (fileType.includes('/')) {
          const mime = fileType
          if (mime === 'application/pdf') return '.pdf'
          if (mime === 'application/msword') return '.doc'
          if (mime === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return '.docx'
          if (mime === 'application/vnd.ms-excel') return '.xls'
          if (mime === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') return '.xlsx'
          if (mime.startsWith('image/')) return `.${mime.split('/')[1]}`
        }
        return `.${fileType}`
      }
      if (fileName.includes('.')) return fileName.substring(fileName.lastIndexOf('.'))
      if (fileUrl.includes('.')) return fileUrl.substring(fileUrl.lastIndexOf('.'))
      return ''
    }

    const ext = getExtension()
    
    // 判断文件类型
    const isExcel = ext === '.xlsx' || ext === '.xls'
    const isWord = ext === '.docx' || ext === '.doc'
    const isPdf = ext === '.pdf'
    const isImage = ext === '.jpg' || ext === '.jpeg' ||
                    ext === '.png' || ext === '.gif' ||
                    ext === '.webp' || ext === '.bmp'
    
    if (isExcel) {
      // Excel文件浏览器无法直接渲染，显示提示信息
      previewType.value = 'unsupported'
      previewUrl.value = ''
      showPreviewDialog.value = true
    } else if (isWord) {
      // Word文档转换为PDF预览（与app端保持一致）
      try {
        const blob = await previewEmployeeDocument(employeeId, row.id, 'pdf')
        if (isMobile.value) {
          previewType.value = 'pdfjs'
          previewUrl.value = ''
          previewBlob.value = blob
          showPreviewDialog.value = true
          await nextTick()
          await renderPdfInPreviewDialog(blob)
        } else {
          previewType.value = 'blob'
          previewUrl.value = URL.createObjectURL(blob)
          showPreviewDialog.value = true
        }
      } catch (error) {
        try {
          if (ext !== '.docx') {
            throw error
          }

          const blob = await previewEmployeeDocument(employeeId, row.id)
          previewType.value = 'docx'
          previewUrl.value = ''
          showPreviewDialog.value = true
          await nextTick()
          if (!docxPreviewContainer.value) {
            throw new Error('docx preview container is not available')
          }
          docxPreviewContainer.value.innerHTML = ''
          const arrayBuffer = await blob.arrayBuffer()
          await renderAsync(arrayBuffer, docxPreviewContainer.value)
        } catch (fallbackError) {
          console.error('Word文档预览失败:', fallbackError)
          ElMessage.error(t('employee.messages.wordPreviewFailed') + ': ' + (await getAxiosErrorDetail(fallbackError)))
          previewType.value = 'unsupported'
          previewUrl.value = ''
          showPreviewDialog.value = true
        }
      }
    } else {
      // PDF、图片等其他文件类型使用blob URL预览
      let blob
      try {
        blob = await previewEmployeeDocument(employeeId, row.id)
      } catch (e) {
        blob = await downloadEmployeeDocument(employeeId, row.id)
      }
      if (isMobile.value && (isPdf || blob?.type === 'application/pdf')) {
        previewType.value = 'pdfjs'
        previewUrl.value = ''
        previewBlob.value = blob
        showPreviewDialog.value = true
        await nextTick()
        await renderPdfInPreviewDialog(blob)
      } else {
        previewType.value = 'blob'
        previewUrl.value = URL.createObjectURL(blob)
        showPreviewDialog.value = true
      }
    }
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error(t('employee.messages.previewFailed') + ': ' + (await getAxiosErrorDetail(error)))
  }
}



const renderPdfForPreview = async (blob) => {
  if (!signaturePreviewPdfContainer.value) {
    console.error('signaturePreviewPdfContainer is not available')
    return
  }
  const container = signaturePreviewPdfContainer.value
  container.innerHTML = ''

  try {
    const pdfjs = await loadPdfjs()
    const data = await blob.arrayBuffer()
    const pdf = await pdfjs.getDocument({ data, disableWorker: true }).promise
    const containerWidth = container.clientWidth || 800
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5)

    const overlayDataUrl = draftSignatureDataUrl.value
    const overlayX =
      currentContractForSign.value?.admin_signature_x ?? currentContractForSign.value?.employee_signature_x
    const overlayY =
      currentContractForSign.value?.admin_signature_y ?? currentContractForSign.value?.employee_signature_y
    const overlayW =
      currentContractForSign.value?.admin_signature_width ?? currentContractForSign.value?.employee_signature_width
    const overlayH =
      currentContractForSign.value?.admin_signature_height ?? currentContractForSign.value?.employee_signature_height
    const overlayPage =
      currentContractForSign.value?.admin_signature_page ?? currentContractForSign.value?.employee_signature_page ?? 0
    const hasOverlayBox =
      overlayDataUrl &&
      overlayX != null &&
      overlayY != null &&
      overlayW != null &&
      overlayH != null &&
      overlayPage != null
    const overlayImg = hasOverlayBox ? await loadImageFromDataUrl(overlayDataUrl) : null

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber)
      const baseViewport = page.getViewport({ scale: 1 })
      const scale = containerWidth / baseViewport.width
      const cssViewport = page.getViewport({ scale })
      const renderViewport = page.getViewport({ scale: scale * dpr })
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = Math.floor(renderViewport.width)
      canvas.height = Math.floor(renderViewport.height)
      canvas.style.width = `${Math.floor(cssViewport.width)}px`
      canvas.style.height = `${Math.floor(cssViewport.height)}px`
      canvas.style.display = 'block'
      canvas.style.margin = '0 auto 16px'
      container.appendChild(canvas)
      await page.render({ canvasContext: context, viewport: renderViewport }).promise

      if (overlayImg && pageNumber - 1 === overlayPage) {
        const boxX = overlayX * cssViewport.width * dpr
        const boxY = overlayY * cssViewport.height * dpr
        const boxW = overlayW * cssViewport.width * dpr
        const boxH = overlayH * cssViewport.height * dpr
        const pad = 2
        const innerW = Math.max(boxW - pad * 2, 1)
        const innerH = Math.max(boxH - pad * 2, 1)
        const scaleImg = Math.min(innerW / Math.max(overlayImg.width, 1), innerH / Math.max(overlayImg.height, 1))
        const drawW = overlayImg.width * scaleImg
        const drawH = overlayImg.height * scaleImg
        let drawX = boxX + pad
        let drawY = boxY + boxH - pad - drawH
        const maxX = boxX + boxW - pad - drawW
        const minY = boxY + pad
        if (drawX > maxX) drawX = maxX
        if (drawY < minY) drawY = minY
        context.drawImage(overlayImg, drawX, drawY, drawW, drawH)

        const dateText = draftSignatureDate.value
        if (dateText) {
          const boxHCss = boxH / dpr
          const gapCss = isMobile.value
            ? Math.max(10, Math.min(boxHCss * 0.22, 20))
            : Math.max(16, Math.min(boxHCss * 0.28, 32))
          const fontSizeCss = isMobile.value
            ? Math.max(12, Math.min(boxHCss * 0.22, 18))
            : Math.max(18, Math.min(boxHCss * 0.32, 30))
          context.save()
          context.fillStyle = '#000'
          context.font = `${Math.round(fontSizeCss * dpr)}px Helvetica, Arial, sans-serif`
          context.textBaseline = 'top'
          const measuredWidth = context.measureText(dateText)?.width
          const textWidth =
            measuredWidth && Number.isFinite(measuredWidth)
              ? measuredWidth
              : dateText.length * Math.round(fontSizeCss * dpr) * 0.6
          let dateX = boxX
          dateX = Math.max(1, Math.min(dateX, canvas.width - textWidth - 1))
          let dateY = boxY + boxH + gapCss * dpr
          const maxY = canvas.height - Math.round(fontSizeCss * dpr) - 1
          if (dateY > maxY) {
            const altY = boxY - gapCss * dpr - Math.round(fontSizeCss * dpr)
            dateY = Math.max(1, Math.min(altY, maxY))
          }
          context.fillText(dateText, dateX, dateY)
          context.restore()
        }
      }
    }
  } catch (error) {
    console.error('PDF预览渲染失败:', error)
    container.innerHTML =
      '<div style="padding: 20px; text-align: center; color: #999;">' +
      t('employee.pdfPreviewRenderFailed', { message: error.message }) +
      '</div>'
  }
}

const renderPdfForPosition = async (blob) => {
  if (!positionPdfContainer.value || !positionPdfCanvasWrapper.value) {
    console.error('positionPdfContainer or positionPdfCanvasWrapper is not available')
    return
  }
  const container = positionPdfContainer.value
  const canvasWrapper = positionPdfCanvasWrapper.value
  canvasWrapper.innerHTML = ''
  pdfContentSize.value = { width: 0, height: 0 }

  try {
    positionPdfSourceBlob.value = blob
    const pdfjs = await loadPdfjs()
    positionPdfBytes.value = await blob.arrayBuffer()
    positionPdfDoc.value = await pdfjs.getDocument({ data: positionPdfBytes.value, disableWorker: true }).promise
    const pdf = positionPdfDoc.value
    const containerWidth = container.clientWidth || canvasWrapper.clientWidth || 800
    let totalHeight = 0
    let maxWidth = 0
    const pageScales = [] // 存储每页的缩放比例和原始尺寸
    const dpr = Math.min(window.devicePixelRatio || 1, 2.5)

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber)
      const baseViewport = page.getViewport({ scale: 1 })
      // 计算缩放比例，确保PDF页面宽度适应容器
      const scale = (containerWidth / baseViewport.width) * positionPdfZoom.value
      const cssViewport = page.getViewport({ scale })
      const renderViewport = page.getViewport({ scale: scale * dpr })
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      canvas.width = Math.floor(renderViewport.width)
      canvas.height = Math.floor(renderViewport.height)
      canvas.style.width = `${Math.floor(cssViewport.width)}px`
      canvas.style.height = `${Math.floor(cssViewport.height)}px`
      canvas.style.display = 'block'
      canvas.style.margin = '0 auto 16px'
      canvasWrapper.appendChild(canvas)
      await page.render({ canvasContext: context, viewport: renderViewport }).promise
      
      // 保存每页的原始尺寸和缩放比例
      pageScales.push({
        pageNumber: pageNumber - 1,
        originalWidth: baseViewport.width,
        originalHeight: baseViewport.height,
        renderedWidth: cssViewport.width,
        renderedHeight: cssViewport.height,
        scale: scale,
        offsetLeft: canvas.offsetLeft,
        offsetTop: totalHeight
      })
      
      maxWidth = Math.max(maxWidth, cssViewport.width)
      totalHeight += cssViewport.height + 16 // 16px是页面间距
    }
    
    // 保存PDF的原始尺寸和渲染尺寸（用于坐标计算）
    // 计算所有页面的最大原始宽度（用于归一化）
    let maxOriginalWidth = 0
    let totalOriginalHeight = 0
    for (const pageInfo of pageScales) {
      maxOriginalWidth = Math.max(maxOriginalWidth, pageInfo.originalWidth)
      totalOriginalHeight += pageInfo.originalHeight + (16 / pageInfo.scale) // 页面间距也要按比例缩放
    }
    
    pdfContentSize.value = {
      width: maxWidth, // 渲染后的宽度
      height: totalHeight, // 渲染后的高度
      originalWidth: maxOriginalWidth, // 原始PDF宽度
      originalHeight: totalOriginalHeight, // 原始PDF高度
      pageScales: pageScales, // 保存每页的缩放信息
      scale: pageScales.length > 0 ? pageScales[0].scale : 1 // 统一的缩放比例
    }
    console.log('PDF rendered successfully, content size:', pdfContentSize.value)
    await nextTick()
    if (positionNormalized.value) {
      restorePositionRect()
    }
  } catch (error) {
    console.error('PDF rendering failed:', error)
    canvasWrapper.innerHTML =
      '<div style="padding: 20px; text-align: center; color: #999;">' +
      t('employee.pdfRenderFailed', { message: error.message }) +
      '</div>'
  }
}

const setPositionSelectionMode = (mode) => {
  positionSelectionMode.value = mode
}

const rerenderPositionPdf = async () => {
  if (!positionPdfSourceBlob.value) return
  await nextTick()
  await renderPdfForPosition(positionPdfSourceBlob.value)
}

const increasePositionPdfZoom = async () => {
  positionPdfZoom.value = Math.min(2.5, Math.round((positionPdfZoom.value + 0.1) * 100) / 100)
  await rerenderPositionPdf()
}

const decreasePositionPdfZoom = async () => {
  positionPdfZoom.value = Math.max(1, Math.round((positionPdfZoom.value - 0.1) * 100) / 100)
  await rerenderPositionPdf()
}

const startPositionSelectFromPoint = (point) => {
  if (!signaturePositionContainer.value) return
  const container = signaturePositionContainer.value
  const rect = container.getBoundingClientRect()

  const scrollbarWidth = container.offsetWidth - container.clientWidth
  const clickX = point.clientX - rect.left
  if (scrollbarWidth > 0 && clickX > container.clientWidth - scrollbarWidth) {
    return
  }

  const clickY = point.clientY - rect.top
  const relativeX = clickX
  const relativeY = clickY
  if (relativeX < 0 || relativeX > container.clientWidth || relativeY < 0 || relativeY > container.clientHeight) return

  isSelectingPosition.value = true
  const contentWidth = pdfContentSize.value.originalWidth || pdfContentSize.value.width || container.scrollWidth
  const contentHeight = pdfContentSize.value.originalHeight || pdfContentSize.value.height || container.scrollHeight
  const scale = pdfContentSize.value.scale || 1
  const renderX = relativeX + container.scrollLeft
  const renderY = relativeY + container.scrollTop

  positionStart.value = { x: renderX, y: renderY, contentWidth, contentHeight, scale }
  positionRect.value = { left: renderX, top: renderY, width: 0, height: 0 }
}

const recomputePositionNormalizedFromRect = () => {
  if (!positionRect.value) return
  const pageIndex = getPageFromRectPosition(positionRect.value.top)
  const pageScales = pdfContentSize.value?.pageScales || []
  const pageInfo = pageScales[pageIndex]
  const contentWidth = pdfContentSize.value.originalWidth
  const contentHeight = pdfContentSize.value.originalHeight
  if (!pageInfo || !contentWidth || !contentHeight) return
  const pageScale = pageInfo.scale || 1
  const offsetLeft = pageInfo.offsetLeft || 0
  const offsetTop = pageInfo.offsetTop || 0
  const xInPageOriginal = (positionRect.value.left - offsetLeft) / pageScale
  const yInPageOriginal = (positionRect.value.top - offsetTop) / pageScale
  const wOriginal = positionRect.value.width / pageScale
  const hOriginal = positionRect.value.height / pageScale
  let pageTopOriginal = 0
  for (let j = 0; j < pageIndex; j += 1) {
    const s = pageScales[j]
    const gapOriginal = 16 / (s?.scale || pageScale)
    pageTopOriginal += (s?.originalHeight || 0) + gapOriginal
  }
  const docX = xInPageOriginal
  const docY = pageTopOriginal + yInPageOriginal
  positionNormalized.value = {
    x: docX / contentWidth,
    y: docY / contentHeight,
    width: wOriginal / contentWidth,
    height: hOriginal / contentHeight,
    page: pageIndex
  }
}

const updatePositionRectFromPoint = (point) => {
  if (!isSelectingPosition.value || !signaturePositionContainer.value) return
  const container = signaturePositionContainer.value
  const rect = container.getBoundingClientRect()
  const clamp = (v, min, max) => Math.max(min, Math.min(v, max))
  const relativeX = clamp(point.clientX - rect.left, 0, rect.width)
  const relativeY = clamp(point.clientY - rect.top, 0, rect.height)
  const currentX = relativeX + container.scrollLeft
  const currentY = relativeY + container.scrollTop

  const absLeft = Math.min(positionStart.value.x, currentX)
  const absTop = Math.min(positionStart.value.y, currentY)
  const absWidth = Math.abs(currentX - positionStart.value.x)
  const absHeight = Math.abs(currentY - positionStart.value.y)
  positionRect.value = { left: absLeft, top: absTop, width: absWidth, height: absHeight }

  if (positionRect.value.width > 0 && positionRect.value.height > 0) {
    recomputePositionNormalizedFromRect()
  }
}

const finishPositionSelection = () => {
  if (!isSelectingPosition.value) return
  isSelectingPosition.value = false

  const currentPage = positionRect.value ? getPageFromRectPosition(positionRect.value.top) : getCurrentPageFromScroll()
  currentPageNumber.value = currentPage
  if (positionNormalized.value) {
    positionNormalized.value.page = currentPage
  }

  if (positionRect.value && (positionRect.value.width < 10 || positionRect.value.height < 10)) {
    const pageScales = pdfContentSize.value?.pageScales || []
    const pageInfo = pageScales[currentPage]
    if (!pageInfo) {
      positionRect.value = null
      positionNormalized.value = null
      return
    }
    const tapX = positionStart.value.x
    const tapY = positionStart.value.y
    const w = Math.min(240, Math.max(120, pageInfo.renderedWidth * 0.5))
    const h = Math.min(110, Math.max(60, pageInfo.renderedHeight * 0.12))
    const leftMin = (pageInfo.offsetLeft || 0)
    const leftMax = leftMin + pageInfo.renderedWidth - w
    const topMin = (pageInfo.offsetTop || 0)
    const topMax = topMin + pageInfo.renderedHeight - h
    const left = Math.max(leftMin, Math.min(tapX - w / 2, leftMax))
    const top = Math.max(topMin, Math.min(tapY - h / 2, topMax))
    positionRect.value = { left, top, width: w, height: h }
    recomputePositionNormalizedFromRect()
  }
}

const handlePositionPointerDown = (event) => {
  if (positionSelectionMode.value !== 'select') return
  if (!signaturePositionContainer.value) return
  if (event.pointerType === 'mouse' && event.button !== 0) return
  positionSelectingPointerId.value = event.pointerId
  try {
    signaturePositionContainer.value.setPointerCapture?.(event.pointerId)
  } catch {}
  event.preventDefault()
  event.stopPropagation()
  startPositionSelectFromPoint(event)
}

const handlePositionPointerMove = (event) => {
  if (positionSelectingPointerId.value !== null && event.pointerId !== positionSelectingPointerId.value) return
  if (!isSelectingPosition.value) return
  event.preventDefault()
  event.stopPropagation()
  updatePositionRectFromPoint(event)
}

const handlePositionPointerUp = (event) => {
  if (positionSelectingPointerId.value !== null && event?.pointerId != null && event.pointerId !== positionSelectingPointerId.value) {
    return
  }
  positionSelectingPointerId.value = null
  try {
    signaturePositionContainer.value?.releasePointerCapture?.(event.pointerId)
  } catch {}
  finishPositionSelection()
}

const getFirstTouchPoint = (touchEvent) => {
  const t = touchEvent?.touches?.[0] || touchEvent?.changedTouches?.[0]
  if (!t) return null
  return { clientX: t.clientX, clientY: t.clientY }
}

const handlePositionTouchStart = (event) => {
  if (positionSelectionMode.value !== 'select') return
  const point = getFirstTouchPoint(event)
  if (!point) return
  event.preventDefault()
  event.stopPropagation()
  startPositionSelectFromPoint(point)
}

const handlePositionTouchMove = (event) => {
  if (positionSelectionMode.value !== 'select') return
  if (!isSelectingPosition.value) return
  const point = getFirstTouchPoint(event)
  if (!point) return
  event.preventDefault()
  event.stopPropagation()
  updatePositionRectFromPoint(point)
}

const handlePositionTouchEnd = (event) => {
  if (positionSelectionMode.value !== 'select') return
  event.preventDefault()
  event.stopPropagation()
  finishPositionSelection()
}

const handlePositionScroll = () => {
  if (!signaturePositionContainer.value) return
  // 仅更新当前页码，positionRect 使用内容坐标，rect 在内容内会随内容自然滚动，无需更新
  const currentPage = getCurrentPageFromScroll()
  currentPageNumber.value = currentPage
  if (positionNormalized.value) {
    positionNormalized.value.page = currentPage
  }
}

const handleDownloadDocument = async (row) => {
  try {
    const blob = await downloadEmployeeDocument(employeeId, row.id)
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', row.name)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success(t('employee.messages.downloadSuccess'))
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error(t('employee.messages.downloadFailed') + ': ' + (error.response?.data?.detail || error.message || t('common.noData')))
  }
}

const handleDeleteDocument = async (row) => {
  try {
    await ElMessageBox.confirm(t('employee.messages.deleteConfirm'), t('common.confirm'), { type: 'warning' })
    await deleteEmployeeDocument(employeeId, row.id)
    ElMessage.success(t('employee.messages.deleteSuccess'))
    // 根据当前菜单重新加载对应的文档列表
    loadDocuments(activeMenu.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(t('employee.messages.deleteFailed') + ': ' + (error.response?.data?.detail || error.message || t('common.noData')))
    }
  }
}

const handleSignContract = (row) => {
  currentContractForSign.value = row
  contractSignatureMethod.value = 0
  contractSignatureFile.value = null
  showContractSignatureDialog.value = true
}

// 开始签字流程
const handleStartSignContract = async (row) => {
  if (row?.admin_signed_at) {
    ElMessage.warning('您已签字请勿重复签名')
    return
  }
  currentContractForSign.value = row
  // 总是从第一步（选择坐标）开始
  signatureFlowStep.value = 0
  contractSignatureSubmitted.value = false
  
  positionRect.value = null
  positionNormalized.value = null
  currentPageNumber.value = 0
  positionPreviewUrl.value = ''
  signaturePreviewUrl.value = ''
  contractSignatureFile.value = null
  contractSignatureMethod.value = 0
  if (contractSignatureCanvas.value) {
    clearCanvas()
  }
  
  showContractSignatureFlowDialog.value = true
  
  // 如果已有坐标，先缓存用于恢复显示
  if (row.admin_signature_x != null && row.admin_signature_y != null) {
    positionNormalized.value = {
      x: row.admin_signature_x,
      y: row.admin_signature_y,
      width: row.admin_signature_width,
      height: row.admin_signature_height,
      page: row.admin_signature_page ?? row.employee_signature_page ?? 0
    }
    currentPageNumber.value = row.admin_signature_page ?? row.employee_signature_page ?? 0
  }
  
  await loadSignaturePositionPreview(row)
}

const handleSelectSignaturePosition = async (row) => {
  currentContractForPosition.value = row
  positionRect.value = null
  positionNormalized.value = null
  currentPageNumber.value = 0
  positionPreviewUrl.value = ''
  showContractSignaturePositionDialog.value = true
  // 如果已有坐标，先缓存用于恢复
  if (row.admin_signature_x != null && row.admin_signature_y != null) {
    positionNormalized.value = {
      x: row.admin_signature_x,
      y: row.admin_signature_y,
      width: row.admin_signature_width,
      height: row.admin_signature_height,
      page: row.admin_signature_page ?? row.employee_signature_page ?? 0
    }
  }
  await loadSignaturePositionPreview(row)
}

const handleContractSignatureFileChange = (file) => {
  contractSignatureFile.value = file.raw
}

const formatToday = () => {
  try {
    return new Date().toISOString().slice(0, 10)
  } catch {
    return ''
  }
}

const loadImageFromDataUrl = (dataUrl) =>
  new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = dataUrl
  })

const trimSignatureDataUrl = async (dataUrl) => {
  if (!dataUrl) return ''
  const img = await loadImageFromDataUrl(dataUrl)
  const canvas = document.createElement('canvas')
  canvas.width = img.width
  canvas.height = img.height
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(img, 0, 0)
  const { data, width, height } = ctx.getImageData(0, 0, canvas.width, canvas.height)
  let minX = width
  let minY = height
  let maxX = -1
  let maxY = -1
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const idx = (y * width + x) * 4
      const r = data[idx]
      const g = data[idx + 1]
      const b = data[idx + 2]
      const a = data[idx + 3]
      if (a <= 10) continue
      if (r >= 245 && g >= 245 && b >= 245) continue
      if (x < minX) minX = x
      if (y < minY) minY = y
      if (x > maxX) maxX = x
      if (y > maxY) maxY = y
    }
  }
  if (maxX < 0 || maxY < 0) return dataUrl
  const outW = Math.max(maxX - minX + 1, 1)
  const outH = Math.max(maxY - minY + 1, 1)
  const out = document.createElement('canvas')
  out.width = outW
  out.height = outH
  const outCtx = out.getContext('2d')
  outCtx.drawImage(canvas, minX, minY, outW, outH, 0, 0, outW, outH)
  return out.toDataURL('image/png')
}

const composeSignatureWithDate = async (signatureDataUrl, dateText) => {
  if (!signatureDataUrl) return ''
  if (!dateText) return signatureDataUrl
  const img = await loadImageFromDataUrl(signatureDataUrl)
  const padding = 12
  const fontSize = 18
  const dateBlockHeight = fontSize + padding * 2
  const canvas = document.createElement('canvas')
  canvas.width = img.width
  canvas.height = img.height + dateBlockHeight
  const ctx = canvas.getContext('2d')
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.drawImage(img, 0, 0)
  ctx.fillStyle = '#000'
  ctx.font = `${fontSize}px sans-serif`
  ctx.textBaseline = 'middle'
  ctx.fillText(dateText, padding, img.height + dateBlockHeight / 2)
  return canvas.toDataURL('image/png')
}

const getDraftSignatureData = async () => {
  const hasPosition =
    currentContractForSign.value?.admin_signature_x != null ||
    currentContractForSign.value?.employee_signature_x != null
  if (!hasPosition) {
    ElMessage.warning('请先选择签字坐标')
    return null
  }
  if (contractSignatureMethod.value === 0) {
    const canvas = contractSignatureCanvas.value
    if (!canvas) {
      ElMessage.warning('请先完成手写签名')
      return null
    }
    const ctx = canvas.getContext('2d')
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const hasContent = imageData.data.some((value, index) => index % 4 === 3 && value !== 0)
    if (!hasContent) {
      ElMessage.warning('请先完成手写签名')
      return null
    }
  } else if (contractSignatureMethod.value === 1 && !contractSignatureFile.value) {
    ElMessage.warning('请选择签名图片')
    return null
  }

  let signatureDataUrl = ''
  if (contractSignatureMethod.value === 1) {
    const reader = new FileReader()
    signatureDataUrl = await new Promise((resolve, reject) => {
      reader.onload = (e) => resolve(e.target.result)
      reader.onerror = reject
      reader.readAsDataURL(contractSignatureFile.value)
    })
  } else {
    const canvas = contractSignatureCanvas.value
    signatureDataUrl = canvas.toDataURL('image/png')
  }

  const dateText = formatToday()
  signatureDataUrl = await trimSignatureDataUrl(signatureDataUrl)
  const submitDataUrl = signatureDataUrl
  return { signatureDataUrl, submitDataUrl, dateText }
}

const fetchPreviewPdfBlobForContract = async () => {
  const fileName = (currentContractForSign.value?.name || '').toLowerCase()
  const fileType = (currentContractForSign.value?.file_type || '').toLowerCase()
  const fileUrl = (currentContractForSign.value?.file_url || '').toLowerCase()

  const getExtension = () => {
    if (fileType) {
      if (fileType.startsWith('.')) return fileType
      if (fileType.includes('/')) {
        const mime = fileType
        if (mime === 'application/pdf') return '.pdf'
        if (mime === 'application/msword') return '.doc'
        if (mime === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return '.docx'
        if (mime === 'application/vnd.ms-excel') return '.xls'
        if (mime === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') return '.xlsx'
        if (mime.startsWith('image/')) return `.${mime.split('/')[1]}`
      }
      return `.${fileType}`
    }
    if (fileName.includes('.')) return fileName.substring(fileName.lastIndexOf('.'))
    if (fileUrl.includes('.')) return fileUrl.substring(fileUrl.lastIndexOf('.'))
    return ''
  }

  const ext = getExtension()
  const isWord = ext === '.docx' || ext === '.doc'
  const isPdf = ext === '.pdf'

  if (isWord) {
    return await previewEmployeeDocument(employeeId, currentContractForSign.value.id, 'pdf')
  }
  if (isPdf) {
    try {
      return await previewEmployeeDocument(employeeId, currentContractForSign.value.id)
    } catch {
      return downloadEmployeeDocument(employeeId, currentContractForSign.value.id)
    }
  }
  try {
    return await previewEmployeeDocument(employeeId, currentContractForSign.value.id, 'pdf')
  } catch {
    return previewEmployeeDocument(employeeId, currentContractForSign.value.id)
  }
}

const previewContractSignature = async () => {
  if (!currentContractForSign.value?.id) return
  contractSignatureUploading.value = true
  try {
    const draft = await getDraftSignatureData()
    if (!draft) return
    draftSignatureDataUrl.value = draft.signatureDataUrl
    draftSignatureSubmitDataUrl.value = draft.submitDataUrl
    draftSignatureDate.value = draft.dateText

    signatureFlowStep.value = 2
    await nextTick()

    const blob = await fetchPreviewPdfBlobForContract()
    if (signaturePreviewUrl.value && signaturePreviewUrl.value.startsWith('blob:')) {
      URL.revokeObjectURL(signaturePreviewUrl.value)
    }
    signaturePreviewUrl.value = URL.createObjectURL(blob)
    if (signaturePreviewPdfContainer.value) {
      signaturePreviewPdfRendered.value = false
      await renderPdfForPreview(blob)
      signaturePreviewPdfRendered.value = true
    }
  } catch (error) {
    console.error('生成预览失败:', error)
    ElMessage.error('生成预览失败: ' + (await getAxiosErrorDetail(error)))
    signaturePreviewPdfRendered.value = false
  } finally {
    contractSignatureUploading.value = false
  }
}

const restartContractSignature = () => {
  draftSignatureDataUrl.value = ''
  draftSignatureSubmitDataUrl.value = ''
  draftSignatureDate.value = ''
  contractSignatureSubmitted.value = false
  contractSignatureFile.value = null
  if (contractSignatureCanvas.value) {
    clearCanvas()
  }
  if (signaturePreviewUrl.value && signaturePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(signaturePreviewUrl.value)
  }
  signaturePreviewUrl.value = ''
  if (signaturePreviewPdfContainer.value) {
    signaturePreviewPdfContainer.value.innerHTML = ''
  }
  signaturePreviewPdfRendered.value = false
  signatureFlowStep.value = 1
}

const confirmContractSignature = async () => {
  if (!currentContractForSign.value?.id) return
  confirmSigning.value = true
  try {
    if (!draftSignatureSubmitDataUrl.value) {
      const draft = await getDraftSignatureData()
      if (!draft) return
      draftSignatureDataUrl.value = draft.signatureDataUrl
      draftSignatureSubmitDataUrl.value = draft.submitDataUrl
      draftSignatureDate.value = draft.dateText
    }

    await signEmployeeContract(employeeId, currentContractForSign.value.id, draftSignatureSubmitDataUrl.value)
    ElMessage.success('签字完成')
    await loadDocuments('contract')
  } catch (error) {
    console.error('确认提交失败:', error)
    ElMessage.error('确认提交失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
    return
  } finally {
    confirmSigning.value = false
  }

  handleCloseSignatureFlowDialog()
}


// 关闭签字流程对话框
const handleCloseSignatureFlowDialog = () => {
  showContractSignatureFlowDialog.value = false
  signatureFlowStep.value = 0
  contractSignatureSubmitted.value = false
  confirmSigning.value = false
  positionRect.value = null
  positionNormalized.value = null
  contractSignatureFile.value = null
  contractSignatureMethod.value = 0
  draftSignatureDataUrl.value = ''
  draftSignatureSubmitDataUrl.value = ''
  draftSignatureDate.value = ''
  // 清理预览URL和PDF容器
  if (signaturePreviewUrl.value && signaturePreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(signaturePreviewUrl.value)
  }
  signaturePreviewUrl.value = ''
  if (signaturePreviewPdfContainer.value) {
    signaturePreviewPdfContainer.value.innerHTML = ''
  }
  signaturePreviewPdfRendered.value = false
  if (positionPreviewUrl.value && positionPreviewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(positionPreviewUrl.value)
  }
  positionPreviewUrl.value = ''
  if (contractSignatureCanvas.value) {
    clearCanvas()
  }
}

const loadSignaturePositionPreview = async (row) => {
  // 支持新的流程和旧的流程
  const targetRow = currentContractForSign.value || row
  try {
    const fileName = (targetRow.name || '').toLowerCase()
    const fileType = (targetRow.file_type || '').toLowerCase()
    const fileUrl = (targetRow.file_url || '').toLowerCase()

    const getExtension = () => {
      if (fileType) {
        if (fileType.startsWith('.')) return fileType
        if (fileType.includes('/')) {
          const mime = fileType
          if (mime === 'application/pdf') return '.pdf'
          if (mime === 'application/msword') return '.doc'
          if (mime === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') return '.docx'
          if (mime === 'application/vnd.ms-excel') return '.xls'
          if (mime === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') return '.xlsx'
          if (mime.startsWith('image/')) return `.${mime.split('/')[1]}`
        }
        return `.${fileType}`
      }
      if (fileName.includes('.')) return fileName.substring(fileName.lastIndexOf('.'))
      if (fileUrl.includes('.')) return fileUrl.substring(fileUrl.lastIndexOf('.'))
      return ''
    }

    const ext = getExtension()
    const isExcel = ext === '.xlsx' || ext === '.xls'
    const isWord = ext === '.docx' || ext === '.doc'
    const isPdf = ext === '.pdf'

    if (isExcel) {
      positionPreviewUrl.value = ''
      return
    }

    const fetchPreviewPdfBlob = async () => {
      if (isWord) {
        try {
          return await previewEmployeeDocument(employeeId, targetRow.id, 'pdf')
        } catch (e) {
          const detail = await getAxiosErrorDetail(e)
          throw new Error('Word 转 PDF 预览失败: ' + detail)
        }
      }
      if (isPdf) {
        try {
          return await previewEmployeeDocument(employeeId, targetRow.id)
        } catch (e) {
          return downloadEmployeeDocument(employeeId, targetRow.id)
        }
      }
      try {
        return await previewEmployeeDocument(employeeId, targetRow.id, 'pdf')
      } catch (e) {
        return previewEmployeeDocument(employeeId, targetRow.id)
      }
    }

    const blob = await fetchPreviewPdfBlob()
    
    // 等待容器准备好
    await nextTick()
    
    // 使用PDF.js渲染PDF，获取实际内容尺寸
    if (positionPdfContainer.value) {
      await renderPdfForPosition(blob)
      
      // 若 positionNormalized 来自 DB（page-level），转换为文档级供 restore 使用
      if (positionNormalized.value && pdfContentSize.value?.pageScales?.length) {
        positionNormalized.value = toDocLevelNormalized(positionNormalized.value)
      }
      
      // 等待PDF渲染完成后再恢复坐标
      await nextTick()
      setTimeout(() => {
        restorePositionRect()
      }, 500)
    } else {
      console.error('positionPdfContainer is not available after nextTick')
      ElMessage.error('PDF容器未准备好，请重试')
    }
  } catch (error) {
    console.error('加载签字坐标预览失败:', error)
    ElMessage.error(t('employee.messages.previewFailed') + ': ' + (await getAxiosErrorDetail(error)))
    positionPreviewUrl.value = ''
  }
}

// 将文档级归一化坐标转换为页内归一化（后端按单页理解）
const toPageLevelNormalized = (docNormalized) => {
  const pageScales = pdfContentSize.value?.pageScales || []
  const pageIndex = docNormalized.page ?? 0
  const pageInfo = pageScales[pageIndex]
  if (!pageInfo) return docNormalized

  const totalOriginalHeight = pdfContentSize.value.originalHeight
  const contentWidth = pdfContentSize.value.originalWidth
  if (!totalOriginalHeight || !contentWidth) return docNormalized

  let pageTopOriginal = 0
  const scale = pdfContentSize.value.scale || 1
  for (let j = 0; j < pageIndex; j++) {
    pageTopOriginal += pageScales[j].originalHeight + (16 / (pageScales[j].scale || scale))
  }

  const docY = docNormalized.y * totalOriginalHeight
  const docHeight = docNormalized.height * totalOriginalHeight
  const docX = docNormalized.x * contentWidth
  const docWidth = docNormalized.width * contentWidth

  const pageLocalY = Math.max(0, Math.min(docY - pageTopOriginal, pageInfo.originalHeight))
  const pageLocalHeight = Math.min(docHeight, pageInfo.originalHeight - pageLocalY)
  const pageNormalizedY = pageLocalY / pageInfo.originalHeight
  const pageNormalizedHeight = Math.max(0.01, Math.min(pageLocalHeight / pageInfo.originalHeight, 1 - pageNormalizedY))
  const pageLocalX = Math.max(0, Math.min(docX, pageInfo.originalWidth))
  const pageLocalWidth = Math.min(docWidth, pageInfo.originalWidth - pageLocalX)
  const pageNormalizedX = pageLocalX / pageInfo.originalWidth
  const pageNormalizedWidth = Math.max(0.01, Math.min(pageLocalWidth / pageInfo.originalWidth, 1 - pageNormalizedX))

  return {
    x: Math.max(0, Math.min(pageNormalizedX, 1)),
    y: Math.max(0, Math.min(pageNormalizedY, 1)),
    width: Math.max(0.01, Math.min(pageNormalizedWidth, 1)),
    height: Math.max(0.01, Math.min(pageNormalizedHeight, 1)),
    page: pageIndex
  }
}

// 将页内归一化坐标转换为文档级（用于从 DB 加载后恢复显示）
const toDocLevelNormalized = (pageNormalized) => {
  const pageScales = pdfContentSize.value?.pageScales || []
  const pageIndex = pageNormalized.page ?? 0
  const pageInfo = pageScales[pageIndex]
  if (!pageInfo) return pageNormalized

  const totalOriginalHeight = pdfContentSize.value.originalHeight
  const contentWidth = pdfContentSize.value.originalWidth
  if (!totalOriginalHeight || !contentWidth) return pageNormalized

  let pageTopOriginal = 0
  const scale = pdfContentSize.value.scale || 1
  for (let j = 0; j < pageIndex; j++) {
    pageTopOriginal += pageScales[j].originalHeight + (16 / (pageScales[j].scale || scale))
  }

  const docY = pageTopOriginal + pageNormalized.y * pageInfo.originalHeight
  const docHeight = pageNormalized.height * pageInfo.originalHeight
  const docX = pageNormalized.x * pageInfo.originalWidth
  const docWidth = pageNormalized.width * pageInfo.originalWidth

  return {
    x: docX / contentWidth,
    y: docY / totalOriginalHeight,
    width: docWidth / contentWidth,
    height: docHeight / totalOriginalHeight,
    page: pageIndex
  }
}

// 更新页码
const updatePageNumber = () => {
  if (positionNormalized.value) {
    positionNormalized.value.page = currentPageNumber.value || 0
  }
}

// 根据滚动位置计算当前页码
const getCurrentPageFromScroll = () => {
  if (!signaturePositionContainer.value || !positionPdfContainer.value) {
    return 0
  }
  const container = signaturePositionContainer.value
  const pdfContainer = positionPdfContainer.value
  const scrollTop = container.scrollTop
  const viewportHeight = container.clientHeight
  const viewportCenter = scrollTop + viewportHeight / 2
  
  // 遍历所有canvas，找到包含视口中心的页面
  const canvases = pdfContainer.querySelectorAll('canvas')
  let offsetTop = 0
  for (let i = 0; i < canvases.length; i++) {
    const canvas = canvases[i]
    const canvasHeight = canvas.offsetHeight
    if (viewportCenter >= offsetTop && viewportCenter < offsetTop + canvasHeight) {
      return i
    }
    offsetTop += canvasHeight + 16 // 16px是页面间距
  }
  
  // 如果没找到，返回最后一页
  return canvases.length > 0 ? canvases.length - 1 : 0
}

// 根据选框的 renderY 计算其所在页码（解决选框与视口中心不在同一页时的错页问题）
const getPageFromRectPosition = (renderY) => {
  const pageScales = pdfContentSize.value?.pageScales || []
  for (let i = 0; i < pageScales.length; i++) {
    const top = pageScales[i].offsetTop
    const bottom = top + pageScales[i].renderedHeight
    if (renderY >= top && renderY < bottom) return i
  }
  return pageScales.length > 0 ? pageScales.length - 1 : 0
}

const restorePositionRect = () => {
  if (!positionNormalized.value || !signaturePositionContainer.value) return
  const container = signaturePositionContainer.value

  const pageScales = pdfContentSize.value?.pageScales || []
  const contentWidth = pdfContentSize.value.originalWidth || container.scrollWidth
  const contentHeight = pdfContentSize.value.originalHeight || container.scrollHeight
  if (!pageScales.length || !contentWidth || !contentHeight) return

  const docX = positionNormalized.value.x * contentWidth
  const docY = positionNormalized.value.y * contentHeight
  const docW = positionNormalized.value.width * contentWidth
  const docH = positionNormalized.value.height * contentHeight

  let pageIndex = typeof positionNormalized.value.page === 'number' ? positionNormalized.value.page : 0
  if (typeof positionNormalized.value.page !== 'number') {
    let acc = 0
    for (let i = 0; i < pageScales.length; i += 1) {
      const s = pageScales[i]
      const gapOriginal = 16 / (s?.scale || 1)
      const start = acc
      const end = acc + (s?.originalHeight || 0)
      if (docY >= start && docY < end) {
        pageIndex = i
        break
      }
      acc += (s?.originalHeight || 0) + gapOriginal
    }
  }
  pageIndex = Math.max(0, Math.min(pageIndex, pageScales.length - 1))
  const pageInfo = pageScales[pageIndex]
  const pageScale = pageInfo.scale || 1
  const offsetLeft = pageInfo.offsetLeft || 0
  const offsetTop = pageInfo.offsetTop || 0

  let pageTopOriginal = 0
  for (let j = 0; j < pageIndex; j += 1) {
    const s = pageScales[j]
    const gapOriginal = 16 / (s?.scale || pageScale)
    pageTopOriginal += (s?.originalHeight || 0) + gapOriginal
  }

  const xInPageOriginal = docX
  const yInPageOriginal = docY - pageTopOriginal
  const renderX = xInPageOriginal * pageScale + offsetLeft
  const renderY = yInPageOriginal * pageScale + offsetTop
  const renderWidth = docW * pageScale
  const renderHeight = docH * pageScale

  positionRect.value = { left: renderX, top: renderY, width: renderWidth, height: renderHeight }

  container.scrollTop = Math.max(0, renderY - container.clientHeight / 2)
}

const handlePositionMouseDown = (event) => {
  if (!signaturePositionContainer.value) return
  const container = signaturePositionContainer.value
  const rect = container.getBoundingClientRect()
  
  // 检查是否点击在滚动条上，如果是则不处理（让滚动条正常工作）
  const scrollbarWidth = container.offsetWidth - container.clientWidth
  const clickX = event.clientX - rect.left
  
  // 如果点击在滚动条区域，不处理（让滚动条正常工作）
  if (scrollbarWidth > 0 && clickX > container.clientWidth - scrollbarWidth) {
    return
  }
  
  // 检查是否点击在容器内容区域
  const clickY = event.clientY - rect.top
  const relativeX = clickX
  const relativeY = clickY
  
  // 如果点击在容器内，开始选择坐标
  if (relativeX >= 0 && relativeX <= container.clientWidth && 
      relativeY >= 0 && relativeY <= container.clientHeight) {
    // 阻止默认行为，开始选择坐标
    event.preventDefault()
    event.stopPropagation()
    isSelectingPosition.value = true
    
    // 使用PDF的原始尺寸进行坐标计算
    let contentWidth = pdfContentSize.value.originalWidth || pdfContentSize.value.width || container.scrollWidth
    let contentHeight = pdfContentSize.value.originalHeight || pdfContentSize.value.height || container.scrollHeight
    
    // 如果PDF内容尺寸未加载，使用容器的滚动尺寸
    if (contentWidth === 0 || contentHeight === 0) {
      contentWidth = container.scrollWidth
      contentHeight = container.scrollHeight
    }
    
    // 获取缩放比例
    const scale = pdfContentSize.value.scale || 1
    
    // 计算相对于PDF内容的绝对坐标（考虑滚动）
    // 注意：relativeX和relativeY是相对于容器可视区域的渲染坐标
    const renderX = relativeX + container.scrollLeft
    const renderY = relativeY + container.scrollTop
    
    positionStart.value = {
      x: renderX,
      y: renderY,
      contentWidth: contentWidth,
      contentHeight: contentHeight,
      scale: scale
    }
    // positionRect 使用内容坐标，rect 在 positionPdfContainer 内会随内容自然滚动
    positionRect.value = {
      left: renderX,
      top: renderY,
      width: 0,
      height: 0
    }
    
  }
}

const handlePositionMouseMove = (event) => {
  if (!isSelectingPosition.value || !signaturePositionContainer.value) return
  // 阻止默认行为，避免与滚动冲突
  event.preventDefault()
  event.stopPropagation()
  const container = signaturePositionContainer.value
  const rect = container.getBoundingClientRect()
  // 计算当前鼠标位置相对于容器的坐标
  const relativeX = event.clientX - rect.left
  const relativeY = event.clientY - rect.top
  // 计算绝对坐标（考虑滚动）
  const currentX = relativeX + container.scrollLeft
  const currentY = relativeY + container.scrollTop
  // 计算选择框的绝对坐标（内容坐标）
  const absLeft = Math.min(positionStart.value.x, currentX)
  const absTop = Math.min(positionStart.value.y, currentY)
  const absWidth = Math.abs(currentX - positionStart.value.x)
  const absHeight = Math.abs(currentY - positionStart.value.y)
  // positionRect 使用内容坐标，rect 在 positionPdfContainer 内会随内容自然滚动
  positionRect.value = {
    left: absLeft,
    top: absTop,
    width: absWidth,
    height: absHeight
  }
  
  // 实时更新归一化坐标用于显示
  if (positionRect.value.width > 0 && positionRect.value.height > 0) {
    const contentWidth = pdfContentSize.value.originalWidth || pdfContentSize.value.width || container.scrollWidth
    const contentHeight = pdfContentSize.value.originalHeight || pdfContentSize.value.height || container.scrollHeight
    const scale = pdfContentSize.value.scale || 1
    
    if (contentWidth > 0 && contentHeight > 0) {
      // positionRect 已是内容坐标 (renderX, renderY)
      const renderX = positionRect.value.left
      const renderY = positionRect.value.top
      const originalX = renderX / scale
      const originalY = renderY / scale
      const originalWidth = positionRect.value.width / scale
      const originalHeight = positionRect.value.height / scale
      
      // 归一化到0-1范围
      positionNormalized.value = {
        x: originalX / contentWidth,
        y: originalY / contentHeight,
        width: originalWidth / contentWidth,
        height: originalHeight / contentHeight,
        page: currentPageNumber.value || 0
      }
    }
  }
}

// 全局鼠标移动和释放事件处理（用于处理鼠标移出容器的情况）
const handleGlobalMouseMove = (event) => {
  if (isSelectingPosition.value) {
    handlePositionMouseMove(event)
  }
}

const handleGlobalMouseUp = () => {
  if (isSelectingPosition.value) {
    handlePositionMouseUp()
  }
}

// 处理鼠标滚轮，在拖动时禁用滚动，否则允许滚动
const handlePositionWheel = (event) => {
  if (isSelectingPosition.value) {
    // 正在选择坐标时，阻止滚动
    event.preventDefault()
    event.stopPropagation()
  }
  // 不在选择坐标时，不阻止默认行为，让容器和滚动条正常处理滚动
}

const handlePositionMouseUp = () => {
  if (!isSelectingPosition.value) return
  isSelectingPosition.value = false
  
  // 移除全局事件监听器
  document.removeEventListener('mousemove', handleGlobalMouseMove)
  document.removeEventListener('mouseup', handleGlobalMouseUp)
  
  // 根据选框位置更新当前页码（若有选框则用选框所在页）
  const currentPage = positionRect.value
    ? getPageFromRectPosition(positionRect.value.top)
    : getCurrentPageFromScroll()
  currentPageNumber.value = currentPage
  if (positionNormalized.value) {
    positionNormalized.value.page = currentPage
  }
  
  // 如果选择框太小，清除选择
  if (positionRect.value && (positionRect.value.width < 10 || positionRect.value.height < 10)) {
    positionRect.value = null
    positionNormalized.value = null
  }
}

// 保存坐标并进入下一步
const handleSavePositionAndNext = async () => {
  if (!positionRect.value || !signaturePositionContainer.value || !currentContractForSign.value) {
    ElMessage.warning('请先选择签字位置')
    return
  }
  try {
    savingSignaturePosition.value = true
    const container = signaturePositionContainer.value
    
    const renderX = positionRect.value.left
    const renderY = positionRect.value.top
    
    // 使用选框实际位置计算页码，而非视口中心
    const currentPage = getPageFromRectPosition(renderY)
    currentPageNumber.value = currentPage
    
    // 使用PDF的原始尺寸进行归一化（文档级）
    let contentWidth = pdfContentSize.value.originalWidth || pdfContentSize.value.width || container.scrollWidth
    let contentHeight = pdfContentSize.value.originalHeight || pdfContentSize.value.height || container.scrollHeight
    
    if (contentWidth === 0 || contentHeight === 0) {
      contentWidth = container.scrollWidth
      contentHeight = container.scrollHeight
    }
    
    const scale = pdfContentSize.value.scale || 1
    const renderWidth = positionRect.value.width
    const renderHeight = positionRect.value.height
    
    const originalX = renderX / scale
    const originalY = renderY / scale
    const originalWidth = renderWidth / scale
    const originalHeight = renderHeight / scale
    
    // 文档级归一化（用于 positionNormalized 和 restore）
    const docNormalized = {
      x: originalX / contentWidth,
      y: originalY / contentHeight,
      width: originalWidth / contentWidth,
      height: originalHeight / contentHeight,
      page: currentPage
    }

    // 转换为页内归一化再保存到 API（后端按单页理解）
    const pageNormalized = toPageLevelNormalized(docNormalized)
    await saveEmployeeContractSignaturePosition(employeeId, currentContractForSign.value.id, pageNormalized)

    currentContractForSign.value.admin_signature_x = pageNormalized.x
    currentContractForSign.value.admin_signature_y = pageNormalized.y
    currentContractForSign.value.admin_signature_width = pageNormalized.width
    currentContractForSign.value.admin_signature_height = pageNormalized.height
    currentContractForSign.value.admin_signature_page = pageNormalized.page ?? 0
    positionNormalized.value = docNormalized

    ElMessage.success('签字坐标已保存')
    signatureFlowStep.value = 1 // 进入下一步：签字
  } catch (error) {
    console.error('保存签字坐标失败:', error)
    ElMessage.error('保存签字坐标失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
  } finally {
    savingSignaturePosition.value = false
  }
}

const saveSignaturePosition = async () => {
  if (!positionRect.value || !signaturePositionContainer.value || !currentContractForPosition.value) {
    return
  }
  try {
    savingSignaturePosition.value = true
    const container = signaturePositionContainer.value
    
    const renderX = positionRect.value.left
    const renderY = positionRect.value.top
    
    // 使用选框实际位置计算页码，而非视口中心
    const currentPage = getPageFromRectPosition(renderY)
    currentPageNumber.value = currentPage
    
    // 使用PDF的原始尺寸进行归一化（文档级）
    let contentWidth = pdfContentSize.value.originalWidth || pdfContentSize.value.width || container.scrollWidth
    let contentHeight = pdfContentSize.value.originalHeight || pdfContentSize.value.height || container.scrollHeight
    
    if (contentWidth === 0 || contentHeight === 0) {
      contentWidth = container.scrollWidth
      contentHeight = container.scrollHeight
    }
    
    const scale = pdfContentSize.value.scale || 1
    const originalX = renderX / scale
    const originalY = renderY / scale
    const originalWidth = positionRect.value.width / scale
    const originalHeight = positionRect.value.height / scale
    
    const docNormalized = {
      x: originalX / contentWidth,
      y: originalY / contentHeight,
      width: originalWidth / contentWidth,
      height: originalHeight / contentHeight,
      page: currentPage
    }

    const pageNormalized = toPageLevelNormalized(docNormalized)
    await saveEmployeeContractSignaturePosition(employeeId, currentContractForPosition.value.id, pageNormalized)

    currentContractForPosition.value.admin_signature_x = pageNormalized.x
    currentContractForPosition.value.admin_signature_y = pageNormalized.y
    currentContractForPosition.value.admin_signature_width = pageNormalized.width
    currentContractForPosition.value.admin_signature_height = pageNormalized.height
    currentContractForPosition.value.admin_signature_page = pageNormalized.page ?? 0
    positionNormalized.value = docNormalized

    ElMessage.success('签字坐标已更新')
    showContractSignaturePositionDialog.value = false
  } catch (error) {
    console.error('保存签字坐标失败:', error)
    ElMessage.error('保存签字坐标失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
  } finally {
    savingSignaturePosition.value = false
  }
}

const handleCloseSignaturePositionDialog = () => {
  if (positionPreviewUrl.value) {
    URL.revokeObjectURL(positionPreviewUrl.value)
  }
  positionPreviewUrl.value = ''
  positionPreviewType.value = ''
  currentContractForPosition.value = null
  positionRect.value = null
  currentPageNumber.value = 0
}

const handleClosePreview = () => {
  // 关闭预览对话框时清理URL
  if (previewType.value === 'blob' && previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  if (previewType.value === 'docx' && docxPreviewContainer.value) {
    docxPreviewContainer.value.innerHTML = ''
  }
  if (previewPdfCanvasWrapper.value) {
    previewPdfCanvasWrapper.value.innerHTML = ''
  }
  previewUrl.value = ''
  previewType.value = ''
  currentPreviewDocument.value = null
  previewBlob.value = null
  previewPdfRenderedKey.value = ''
}

// 任务相关方法
const loadEmployeeTasks = async () => {
  tasksLoading.value = true
  try {
    const params = { assigned_employee_id: employeeId }
    // 只显示该员工已领取的任务，排除待领取状态
    // 如果用户选择了状态筛选，使用用户选择的状态；否则不传status参数，后端会返回所有已领取的任务
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    const allTasks = await getTasks(params)
    // 双重验证：确保只显示该员工已领取的任务
    // 1. 过滤掉待领取状态的任务
    // 2. 确保任务的assigned_employee_id确实等于当前员工ID
    employeeTasks.value = allTasks.filter(task => {
      // 必须是该员工的任务
      const isEmployeeTask = task.assigned_employee_id === employeeId
      // 必须不是待领取状态（已领取的任务）
      const isClaimed = task.status !== 'pending'
      return isEmployeeTask && isClaimed
    })
  } catch (error) {
    ElMessage.error(t('employee.messages.loadTasksFailed'))
  } finally {
    tasksLoading.value = false
  }
}

const getTaskStatusType = (status) => {
  const map = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    rejected: 'danger',
    approved: 'success',
    cancelled: 'info'
  }
  return map[status] || ''
}

const getTaskStatusText = (status) => {
  const map = {
    pending: t('employee.taskStatus.pending'),
    in_progress: t('employee.taskStatus.inProgress'),
    completed: t('employee.taskStatus.completed'),
    rejected: t('employee.taskStatus.rejected'),
    approved: t('employee.taskStatus.approved'),
    cancelled: t('employee.taskStatus.cancelled')
  }
  return map[status] || status
}

const handleViewTask = (row) => {
  router.push(`/tasks/${row.id}`)
}

const getUploadDialogTitle = () => {
  const titles = {
    contract: t('employee.uploadDialog.contract'),
    checklist: t('employee.uploadDialog.checklist'),
    code: t('employee.uploadDialog.code'),
    tracker: t('employee.uploadDialog.tracker'),
    onboarding: t('employee.uploadDialog.onboarding')
  }
  return titles[currentUploadType.value] || t('employee.uploadDialog.default')
}

const handleGenerateContract = async () => {
  if (!contractFormRef.value) return
  
  await contractFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    contractGenerating.value = true
    try {
      // 格式化工作时间
      let workHoursStr = ''
      if (contractForm.work_hours && Array.isArray(contractForm.work_hours) && contractForm.work_hours.length === 2) {
        // 将时间格式从 HH:mm 转换为 12小时制，如 "9 am to 5 pm"
        const formatTime = (timeStr) => {
          const [hours, minutes] = timeStr.split(':')
          const hour = parseInt(hours)
          const min = parseInt(minutes)
          if (hour === 0) {
            return `12:${min.toString().padStart(2, '0')} am`
          } else if (hour < 12) {
            return `${hour}:${min.toString().padStart(2, '0')} am`
          } else if (hour === 12) {
            return `12:${min.toString().padStart(2, '0')} pm`
          } else {
            return `${hour - 12}:${min.toString().padStart(2, '0')} pm`
          }
        }
        workHoursStr = `${formatTime(contractForm.work_hours[0])} to ${formatTime(contractForm.work_hours[1])}`
      }
      
      const contractData = {
        start_date: contractForm.start_date,
        employment_type: contractForm.employment_type,
        position: contractForm.position,
        superior_first_name: contractForm.superior_first_name,
        superior_last_name: contractForm.superior_last_name,
        superior_title: contractForm.superior_title,
        hours_per_week: contractForm.hours_per_week,
        work_hours: workHoursStr,
        gross_salary: contractForm.gross_salary,
        signature_date: contractForm.signature_date
      }
      
      const generated = await generateEmployeeContract(employeeId, contractData)
      ElMessage.success(t('employee.messages.generateContractSuccess'))
      showContractForm.value = false
      // 重置表单
      Object.assign(contractForm, {
        start_date: '',
        employment_type: '',
        position: '',
        superior_first_name: '',
        superior_last_name: '',
        superior_title: '',
        hours_per_week: null,
        work_hours: null,
        gross_salary: null,
        signature_date: ''
      })
      // 重新加载文档列表
      await loadDocuments('contract')

    } catch (error) {
      console.error('生成合同失败:', error)
      ElMessage.error(t('employee.messages.generateContractFailed') + ': ' + (error.response?.data?.detail || error.message || t('common.noData')))
    } finally {
      contractGenerating.value = false
    }
  })
}

// 监听路由参数变化，更新activeMenu
watch(() => route.query.tab, (newTab) => {
  if (!newTab) return
  const normalizedTab = newTab === 'training' ? 'qualifications' : newTab
  if (allowedTabs.includes(normalizedTab)) {
    if (activeMenu.value === normalizedTab && newTab !== 'training') return
    activeMenu.value = normalizedTab
    if (newTab === 'training') {
      qualificationActiveTab.value = 'training'
    }
    if (normalizedTab === 'tasks') {
      loadEmployeeTasks()
    } else if (normalizedTab === 'qualifications') {
      loadReminderSetting()
      loadQualificationsPanel()
      markQualificationReadIfNeeded()
    } else if (['contract', 'code', 'onboarding'].includes(normalizedTab)) {
      loadDocuments(normalizedTab)
    }
  }
}, { immediate: false })

watch(() => route.query.qualificationTab, (newTab) => {
  if (!newTab) return
  qualificationActiveTab.value = newTab
  if (activeMenu.value === 'qualifications') {
    loadQualificationsPanel()
  }
}, { immediate: false })

onMounted(() => {
  loadEmployee()
  markUpdatesRead('employee', employeeId).catch(() => {})
  if (['contract', 'code', 'onboarding', 'handbook'].includes(activeMenu.value)) {
    loadDocuments(activeMenu.value)
  } else if (activeMenu.value === 'tasks') {
    loadEmployeeTasks()
  } else if (activeMenu.value === 'qualifications') {
    loadReminderSetting()
    loadQualificationsPanel()
    markQualificationReadIfNeeded()
  }
})
</script>

<style scoped>
.employee-detail {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.basic-info {
  margin-bottom: 24px;
}
.employee-name {
  color: var(--el-color-primary);
  font-weight: 700;
}

.content-section {
  padding: 0;
}

.tab-label-with-dot {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
}

.section-title {
  margin: 0 0 24px 0;
  font-size: 26px;
  font-weight: 600;
  color: #0f172a;
  padding-bottom: 12px;
  border-bottom: 2px solid #e6eaf2;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e4e7ed;
}
.section-header--right {
  justify-content: flex-end;
}

.section-header .section-title {
  margin: 0;
  border: none;
  padding: 0;
}

.operations-panel {
  padding: 20px 0;
}

.filter-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.signature-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: nowrap;
}

:deep(.el-table) {
  border-radius: 4px;
  overflow: hidden;
}

:deep(.el-table th) {
  background-color: #ffffff;
  font-weight: 600;
}

:deep(.el-descriptions) {
  border-radius: 4px;
  overflow: hidden;
  --el-descriptions-item-label-font-size: var(--el-font-size-base);
  --el-descriptions-item-content-font-size: var(--el-font-size-base);
}

:deep(.el-descriptions__label) {
  font-weight: 500;
  background-color: #f5f7fa;
}

:deep(.el-descriptions__label),
:deep(.el-descriptions__content) {
  font-size: var(--el-font-size-base) !important;
}

:deep(.el-descriptions__cell) {
  font-size: var(--el-font-size-base) !important;
}
.signature-position-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  position: sticky;
  top: 0;
  z-index: 5;
  background: #fff;
  padding: 8px 0;
}

.signature-position-toolbar-left,
.signature-position-toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.signature-position-toolbar-right .zoom-text {
  min-width: 60px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.signature-position-container {
  position: relative;
  width: 100%;
  height: 80vh;
  background: #f5f7fa;
  overflow: auto;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  -webkit-overflow-scrolling: touch;
}

.signature-position-container.select-mode {
  touch-action: none;
  user-select: none;
  overscroll-behavior: contain;
}

.signature-position-docx {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #fff;
}

.signature-position-pdf {
  position: relative;
  width: 100%;
  min-height: 100%;
  background: #fff;
}

.position-pdf-canvases {
  width: 100%;
  min-height: 100%;
}

.signature-position-image {
  width: 100%;
  display: block;
  background: #fff;
}

.signature-position-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

.signature-position-overlay {
  position: absolute;
  top: 0;
  left: 0;
  /* 不覆盖滚动条区域，让滚动条可以正常操作 */
  width: calc(100% - 17px); /* 减去滚动条宽度 */
  height: 100%;
  z-index: 1; /* 在PDF容器之上，但在选择框之下 */
  cursor: crosshair;
  pointer-events: auto;
  background: transparent;
}

.signature-position-overlay.selecting {
  cursor: crosshair;
  /* 选择时阻止滚动 */
  user-select: none;
}

.signature-position-unsupported {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  font-size: 14px;
}

.signature-flow-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
  padding: 20px 0;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #e4e7ed;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
  transition: all 0.3s;
}

.step-item.active .step-number {
  background-color: #409eff;
  color: #fff;
}

.step-item.completed .step-number {
  background-color: #67c23a;
  color: #fff;
}

.step-label {
  margin-top: 8px;
  font-size: 14px;
  color: #909399;
  transition: all 0.3s;
}

.step-item.active .step-label {
  color: #409eff;
  font-weight: 500;
}

.step-item.completed .step-label {
  color: #67c23a;
}

.step-connector {
  width: 100px;
  height: 2px;
  background-color: #e4e7ed;
  margin: 0 10px;
  transition: all 0.3s;
}

.step-connector.completed {
  background-color: #67c23a;
}

.signature-flow-content {
  min-height: 500px;
  padding: 20px 0;
}

.step-content {
  width: 100%;
}

.selected-position-info {
  margin-top: 20px;
  padding: 0 20px;
}

.selected-position-info .el-card {
  background-color: #f5f7fa;
}

.preview-container {
  width: 100%;
  min-height: 600px;
  max-height: 80vh;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: auto;
  background: #fff;
}

.signature-preview-pdf {
  width: 100%;
  min-height: 100%;
  background: #fff;
  padding: 20px 0;
}

.signature-preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.preview-loading .el-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.signature-position-rect {
  position: absolute;
  border: 2px solid #409eff;
  background: rgba(64, 158, 255, 0.15);
  pointer-events: none;
  z-index: 2; /* 在覆盖层之上 */
}

.preview-wrapper {
  position: relative;
  width: 100%;
  height: 80vh;
  overflow: auto;
  background: #fff;
}

.preview-docx {
  width: 100%;
  min-height: 100%;
  padding: 20px;
  background: #fff;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

.preview-pdfjs {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #fff;
}

.preview-pdfjs-canvases {
  padding: 16px 0;
}

.preview-unsupported,
.preview-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  flex-direction: column;
}

.page-number-form-item {
  margin-top: 10px;
}

.page-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

</style>
