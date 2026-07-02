<template>
  <div class="questionnaire-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>{{ pageTitle }}</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            {{ $t('questionnaire.createQuestionnaire') }}
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select
          v-model="titleFilter"
          :placeholder="$t('questionnaire.title')"
          clearable
          filterable
          allow-create
          default-first-option
          :style="{ width: isMobile ? '100%' : '320px' }"
          @change="handleFilterChange"
        >
          <el-option v-for="opt in titleOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
        <el-button type="primary" @click="handleSearch">{{ $t('common.search') }}</el-button>
        <el-button @click="handleReset">{{ $t('task.reset') }}</el-button>
      </div>
      
      <el-table :data="pagedQuestionnaires" v-loading="loading" stripe>
        <el-table-column :label="$t('questionnaire.title')">
          <template #default="{ row }">
            {{ resolveLocalizedText(row?.title_i18n, row?.title) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('questionnaire.description')">
          <template #default="{ row }">
            {{ resolveLocalizedText(row?.description_i18n, row?.description) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" :label="$t('questionnaire.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? $t('questionnaire.enabled') : $t('questionnaire.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('questionnaire.operations')" width="200" :fixed="isMobile ? false : 'right'">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">{{ $t('questionnaire.edit') }}</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">{{ $t('questionnaire.delete') }}</el-button>
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
defineOptions({
  name: 'Questionnaires'
})
import { ref, onMounted, computed, inject, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getQuestionnaires, deleteQuestionnaire } from '@/api/questionnaires'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const isMobile = inject('isMobile', ref(false))
const router = useRouter()
const questionnaires = ref([])
const loading = ref(false)
const titleFilter = ref('')
const page = ref(1)
const pageSize = ref(10)

const pageTitle = computed(() => {
  const base = t('menu.questionnaires')
  const sub = t('questionnaire.templates')
  return `${base}/${sub}`
})

const normalizeString = (v) => (v == null ? '' : String(v)).trim()
const includesText = (source, keyword) => {
  const s = normalizeString(source).toLowerCase()
  const k = normalizeString(keyword).toLowerCase()
  if (!k) return true
  return s.includes(k)
}

const getQuestionnaireTitle = (row) => resolveLocalizedText(row?.title_i18n, row?.title)

const titleOptions = computed(() => {
  const list = Array.isArray(questionnaires.value) ? questionnaires.value : []
  return list
    .map((q) => ({ value: getQuestionnaireTitle(q), label: getQuestionnaireTitle(q) || '-' }))
    .filter((opt) => normalizeString(opt.value))
    .sort((a, b) => a.label.localeCompare(b.label))
})

const filteredQuestionnaires = computed(() => {
  const list = Array.isArray(questionnaires.value) ? questionnaires.value : []
  const keyword = normalizeString(titleFilter.value)
  if (!keyword) return list
  return list.filter((q) => includesText(getQuestionnaireTitle(q), keyword))
})

const total = computed(() => filteredQuestionnaires.value.length)
const pagedQuestionnaires = computed(() => {
  const list = filteredQuestionnaires.value
  const p = Number(page.value) || 1
  const size = Number(pageSize.value) || 10
  const start = (p - 1) * size
  return list.slice(start, start + size)
})

const loadQuestionnaires = async () => {
  loading.value = true
  try {
    questionnaires.value = await getQuestionnaires()
  } catch (error) {
    ElMessage.error(t('questionnaire.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  page.value = 1
}

const handleSearch = () => {
  page.value = 1
}

const handleReset = () => {
  titleFilter.value = ''
  page.value = 1
}

const handleAdd = () => {
  router.push('/questionnaires/new')
}

const handleEdit = (row) => {
  router.push(`/questionnaires/${row.id}`)
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('questionnaire.deleteConfirm'), t('questionnaire.tip'), { type: 'warning' })
    await deleteQuestionnaire(row.id)
    ElMessage.success(t('questionnaire.deleteSuccess'))
    loadQuestionnaires()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('questionnaire.deleteFailed'))
    }
  }
}

onMounted(() => {
  loadQuestionnaires()
})

watch(titleFilter, () => {
  page.value = 1
})

function resolveLocalizedText(i18nValue, fallback = '') {
  const lang = String(locale.value || 'zh').toLowerCase().startsWith('en') ? 'en' : 'zh'
  if (i18nValue && typeof i18nValue === 'object') {
    const direct = String(i18nValue[lang] || '').trim()
    const alternate = String(i18nValue[lang === 'zh' ? 'en' : 'zh'] || '').trim()
    if (direct) return direct
    if (alternate) return alternate
  }
  return String(fallback || '').trim()
}
</script>

<style scoped>
.questionnaire-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.pager-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
