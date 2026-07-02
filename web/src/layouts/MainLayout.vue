<template>
  <el-container class="layout-container">
    <el-aside :width="(isCollapsed && !isMobile) ? '60px' : '220px'" class="sidebar" :class="{ 'sidebar-collapsed': isCollapsed && !isMobile, 'sidebar-mobile-hidden': isMobile && !sidebarVisible }">
      <div class="logo">
        <img
          class="logo-img"
          :class="{ 'logo-img--expanded': !isCollapsed }"
          :src="isCollapsed ? logoIcon : logoTitle"
          alt="logo"
        />
        <el-button
          type="text"
          class="collapse-btn"
          @click="toggleSidebar"
          :title="isCollapsed ? $t('layout.expand') : $t('layout.collapse')"
        >
          <el-icon><ArrowLeft v-if="!isCollapsed" /><ArrowRight v-else /></el-icon>
        </el-button>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        :collapse="isCollapsed"
        background-color="#072655"
        text-color="#ffffff"
        active-text-color="#072655"
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <span>{{ $t('menu.dashboard') }}</span>
        </el-menu-item>
        <el-menu-item index="/employees">
          <el-icon><User /></el-icon>
          <span class="menu-item-with-dot">
            <span>{{ $t('menu.employees') }}</span>
            <span v-if="((updateCounts.employee || 0) + (updateCounts.employee_qualification || 0)) > 0" class="menu-dot-corner" />
          </span>
        </el-menu-item>
        <el-sub-menu index="/customers">
          <template #title>
            <el-icon><Avatar /></el-icon>
            <span class="menu-item-with-dot">
              <span>{{ $t('menu.customers') }}</span>
              <span v-if="((updateCounts.customer || 0) + (updateCounts.customer_pending || 0)) > 0" class="menu-dot-corner" />
            </span>
          </template>
          <el-menu-item index="/customers/built">{{ $t('customer.builtTab') }}</el-menu-item>
          <el-menu-item index="/customers/not-built">{{ $t('customer.notBuiltTab') }}</el-menu-item>
          <el-menu-item index="/customers/pending">
            <span class="menu-item-with-dot">
              <span>{{ $t('customer.pendingTab') }}</span>
              <span v-if="(updateCounts.customer_pending || 0) > 0" class="menu-dot-corner" />
            </span>
          </el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/tasks">
          <template #title>
            <el-icon><Document /></el-icon>
            <span class="menu-item-with-dot">
              <span>{{ $t('menu.tasks') }}</span>
              <span v-if="(updateCounts.task || 0) > 0" class="menu-dot-corner" />
            </span>
          </template>
          <el-menu-item index="/tasks/all">{{ $t('invoice.allTab') }}</el-menu-item>
          <el-menu-item index="/tasks/issued">{{ $t('invoice.issuedTab') }}</el-menu-item>
          <el-menu-item index="/tasks/unissued">{{ $t('invoice.unissuedTab') }}</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/questionnaires">
          <template #title>
            <el-icon><EditPen /></el-icon>
            <span>{{ $t('menu.questionnaires') }}</span>
          </template>
          <el-menu-item index="/questionnaires/templates">{{ $t('questionnaire.templates') }}</el-menu-item>
          <el-menu-item index="/questionnaires/submissions">{{ $t('questionnaire.submissions') }}</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/leave-requests">
          <el-icon><Calendar /></el-icon>
          <span class="menu-item-with-dot">
            <span>{{ $t('menu.leaveRequests') }}</span>
            <span v-if="(updateCounts.leave_request || 0) > 0" class="menu-dot-corner" />
          </span>
        </el-menu-item>
        <el-menu-item index="/invoice-services">
          <el-icon><Setting /></el-icon>
          <span>{{ $t('menu.invoiceServices') }}</span>
        </el-menu-item>
        <el-sub-menu index="/incident-templates">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>{{ $t('menu.incidentTemplates') }}</span>
          </template>
          <el-menu-item index="/incident-templates/templates">{{ $t('incidentTemplate.templates') }}</el-menu-item>
          <el-menu-item index="/incident-templates/submissions">{{ $t('incidentTemplate.submissions') }}</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/task-record-templates">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>{{ $t('menu.taskRecordTemplates') }}</span>
          </template>
          <el-menu-item index="/task-record-templates/templates">{{ $t('taskRecordTemplate.templates') }}</el-menu-item>
          <el-menu-item index="/task-record-templates/submissions">{{ $t('taskRecordTemplate.submissions') }}</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/template-files">
          <el-icon><Document /></el-icon>
          <span>{{ $t('menu.templateFiles') }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span class="header-title">{{ $t('layout.title') }}</span>
        </div>
        <el-button v-if="isMobile" class="menu-toggle" @click="sidebarVisible = !sidebarVisible" text>
          <el-icon><Menu /></el-icon>
        </el-button>
        <div v-if="isMobile && sidebarVisible" class="sidebar-overlay" @click="sidebarVisible = false" />
        <div class="header-right">
          <el-button text @click="loadUpdateSummary" style="margin-right: 6px;">
            <el-icon><Refresh /></el-icon>
          </el-button>
          <el-select
            v-model="currentLocale"
            @change="handleLocaleChange"
            style="width: 96px; margin-right: 12px;"
            size="default"
          >
            <el-option :label="$t('common.chinese')" value="zh" />
            <el-option :label="$t('common.english')" value="en" />
          </el-select>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ $t('common.admin') }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">{{ $t('common.logout') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view v-slot="{ Component, route }">
          <keep-alive :include="['Dashboard', 'Employees', 'Customers', 'Tasks', 'Questionnaires', 'Invoices', 'TemplateFiles', 'IncidentTemplates', 'TaskRecordTemplates']">
            <component :is="Component" :key="route.name" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useI18nStore } from '@/stores/i18n'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Menu, Refresh } from '@element-plus/icons-vue'
import logoIcon from '@/assets/logo.png'
import logoTitle from '@/assets/logo color.png'
import { getUpdateSummary } from '@/api/updates'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { locale } = useI18n()
const i18nStore = useI18nStore()

const activeMenu = computed(() => route.path)
const currentLocale = ref(locale.value)
const isCollapsed = ref(false)
const isMobile = ref(window.innerWidth < 768)
const sidebarVisible = ref(false)
const updateCounts = ref({})

provide('isMobile', isMobile)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

const onResize = () => {
  isMobile.value = window.innerWidth < 768
  if (!isMobile.value) sidebarVisible.value = false
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  window.addEventListener('updates-changed', loadUpdateSummary)
  loadUpdateSummary()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('updates-changed', loadUpdateSummary)
})

const loadUpdateSummary = async () => {
  try {
    const res = await getUpdateSummary()
    updateCounts.value = res?.counts || {}
  } catch {
    updateCounts.value = updateCounts.value || {}
  }
}

onMounted(() => {
  currentLocale.value = locale.value
})

const handleLocaleChange = (value) => {
  i18nStore.setLocale(value)
  currentLocale.value = value
  ElMessage.success(t('common.languageSwitched'))
}

const handleCommand = (command) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
    ElMessage.success(t('common.logout'))
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #072655;
  overflow: hidden;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.1);
  transition: width 0.3s ease, transform 0.3s ease;
  border-right: 1px solid #e5e6eb;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    height: 100vh;
    z-index: 1001;
    width: 220px !important;
  }
  .sidebar-mobile-hidden {
    transform: translateX(-100%);
  }
  .menu-toggle {
    margin-right: 12px;
  }
  .main-content {
    padding: 16px;
  }

  .header {
    padding: 0 12px;
    gap: 8px;
  }

  .header-title {
    font-size: var(--el-font-size-large);
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .header-right {
    gap: 8px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .user-info {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :deep(.header-right .el-select) {
    width: 92px !important;
    margin-right: 0 !important;
  }
}

.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.sidebar-collapsed {
  width: 60px !important;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  color: #1d2129;
  background: #ffffff;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
  transition: all 0.3s ease;
  padding: 0 12px;
}

.logo-img {
  width: 22px;
  height: 22px;
  display: block;
  margin: 0 auto;
  object-fit: contain;
}

.logo-img--expanded {
  width: auto;
  height: 48px;
  max-width: 180px;
}

.collapse-btn {
  position: absolute;
  right: 8px;
  color: #909399;
  font-size: var(--el-font-size-medium);
  padding: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  border-radius: 4px;
}

.sidebar-collapsed .collapse-btn {
  right: 50%;
  transform: translateX(50%);
}

.sidebar-menu {
  border: none;
  height: calc(100vh - 64px);
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

.sidebar-menu.el-menu--collapse {
  width: 90%;
}

:deep(.el-menu--collapse .el-menu-item span) {
  height: 0;
  width: 0;
  overflow: hidden;
  visibility: hidden;
  display: inline-block;
}

:deep(.el-menu--collapse .el-menu-item .el-icon) {
  margin-right: 0;
}

:deep(.sidebar-menu.el-menu--collapse .el-menu-item) {
  width: 100%;
  margin: 8px 0;
  border-radius: 0;
  padding: 0 !important;
  justify-content: center;
}

.sidebar-menu::-webkit-scrollbar {
  width: 6px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

/* 导航项样式增强：更大间距与字体 */
:deep(.sidebar-menu .el-menu-item) {
  height: 56px;
  line-height: 56px;
  margin: 6px 6px;
  border-radius: var(--border-radius-md);
  font-size: var(--el-font-size-medium);
  color: #ffffff;
}

:deep(.sidebar-menu .el-menu-item .el-icon) {
  margin-right: 10px;
  font-size: var(--el-font-size-medium);
  color: #ffffff;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: #2A456D;
  color: #ffffff;
}

:deep(.sidebar-menu .el-menu-item.is-active .el-icon) {
  color: #ffffff;
}
 
:deep(.sidebar-menu .el-menu-item.is-active:hover) {
  background: #2A456D;
}

:deep(.sidebar-menu .el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.08);
}

:deep(.sidebar-menu .el-sub-menu__title) {
  height: 56px;
  line-height: 56px;
  margin: 6px 6px;
  border-radius: var(--border-radius-md);
  font-size: var(--el-font-size-medium);
  color: #ffffff;
}

:deep(.sidebar-menu .el-sub-menu__title .el-icon) {
  margin-right: 10px;
  font-size: var(--el-font-size-medium);
  color: #ffffff;
}

:deep(.sidebar-menu .el-sub-menu__title .el-sub-menu__icon-arrow) {
  font-size: var(--el-font-size-small);
  color: #ffffff;
}

:deep(.sidebar-menu .el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.08);
}

:deep(.sidebar-menu .el-sub-menu.is-active > .el-sub-menu__title) {
  background: #2A456D;
  color: #ffffff;
}

:deep(.sidebar-menu .el-sub-menu.is-active > .el-sub-menu__title .el-icon),
:deep(.sidebar-menu .el-sub-menu.is-active > .el-sub-menu__title .el-sub-menu__icon-arrow) {
  color: #ffffff;
}
 
:deep(.sidebar-menu .el-sub-menu.is-active > .el-sub-menu__title:hover) {
  background: #2A456D;
}

:deep(.sidebar-menu .el-sub-menu .el-menu-item) {
  height: 40px;
  line-height: 40px;
  margin: 4px 12px;
  border-radius: var(--border-radius-md);
  font-size: var(--el-font-size-small);
}

:deep(.sidebar-menu .el-sub-menu .el-menu-item.is-active) {
  background: #f7f7f7;
  color: #072655;
}
 
:deep(.sidebar-menu .el-sub-menu .el-menu-item.is-active:hover) {
  background: #f7f7f7;
}

:deep(.sidebar-menu .el-sub-menu .el-menu-item:hover) {
  background: #f3f6fb;
  color: #072655;
}

:deep(.el-menu--collapse .el-sub-menu__title span) {
  height: 0;
  width: 0;
  overflow: hidden;
  visibility: hidden;
  display: inline-block;
}

:deep(.el-menu--collapse .el-sub-menu__title .el-icon) {
  margin-right: 0;
}

.header {
  background-color: var(--header-bg);
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 16px;
  box-shadow: var(--box-shadow-sm);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-title {
  font-size: var(--el-font-size-extra-large);
  font-weight: 700;
  color: #0f172a;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #606266;
}

.user-info .el-icon {
  margin-right: 5px;
}

.menu-item-with-dot {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 100%;
  padding-right: 18px;
}

.menu-dot-corner {
  position: absolute;
  top: 6px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
}

.main-content {
  background-color: var(--main-bg);
  padding: 20px;
  min-height: calc(100vh - 64px);
}
</style>
