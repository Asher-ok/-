<template>
  <div class="template-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            {{ $t('taskRecordTemplates.create') }}
          </el-button>
        </div>
      </template>

      <el-table :data="pagedRows" v-loading="loading" stripe>
        <el-table-column :label="$t('taskRecordTemplates.title')">
          <template #default="{ row }">
            {{ resolveLocalizedText(row?.title_i18n, row?.title) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" :label="$t('taskRecordTemplates.status')" width="110">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? $t('taskRecordTemplates.enabled') : $t('taskRecordTemplates.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('taskRecordTemplates.operations')" width="220" :fixed="isMobile ? false : 'right'">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">{{ $t('taskRecordTemplates.edit') }}</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">{{ $t('taskRecordTemplates.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager-bar">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10]"
          layout="total, prev, pager, next"
          :total="total"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
defineOptions({ name: 'TaskRecordTemplates' })
import { ref, computed, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getTaskRecordTemplates, deleteTaskRecordTemplate } from '@/api/taskRecordTemplates'

const { t, locale } = useI18n()
const isMobile = inject('isMobile', ref(false))
const router = useRouter()

const rows = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)

const pageTitle = computed(() => `${t('menu.taskRecordTemplates')}/${t('taskRecordTemplate.templates')}`)

const total = computed(() => (Array.isArray(rows.value) ? rows.value.length : 0))
const pagedRows = computed(() => {
  const list = Array.isArray(rows.value) ? rows.value : []
  const p = Number(page.value) || 1
  const size = Number(pageSize.value) || 10
  const start = (p - 1) * size
  return list.slice(start, start + size)
})

const normalizeString = (v) => (v == null ? '' : String(v)).trim()
function resolveLocalizedText(i18nValue, fallback = '') {
  const lang = String(locale.value || 'zh').toLowerCase().startsWith('en') ? 'en' : 'zh'
  if (i18nValue && typeof i18nValue === 'object') {
    const direct = normalizeString(i18nValue[lang])
    const alternate = normalizeString(i18nValue[lang === 'zh' ? 'en' : 'zh'])
    if (direct) return direct
    if (alternate) return alternate
  }
  return normalizeString(fallback)
}

const load = async () => {
  loading.value = true
  try {
    const res = await getTaskRecordTemplates()
    rows.value = Array.isArray(res) ? res : (res?.items || res?.data || [])
  } catch (e) {
    ElMessage.error(e?.message || t('taskRecordTemplates.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  router.push('/task-record-templates/templates/new')
}

const handleEdit = (row) => {
  router.push(`/task-record-templates/templates/${row.id}`)
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('taskRecordTemplates.deleteConfirm'), t('taskRecordTemplates.tip'), { type: 'warning' })
    await deleteTaskRecordTemplate(row.id)
    ElMessage.success(t('taskRecordTemplates.deleteSuccess'))
    load()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(t('taskRecordTemplates.deleteFailed'))
    }
  }
}

load()
</script>

<style scoped>
.template-list {
  padding: 20px;
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
</style>
