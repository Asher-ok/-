<template>
  <div class="dashboard">
    <!-- 第一行：统计卡片 -->
    <el-row :gutter="12" class="mb-20">
      <el-col :span="6" :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409EFF;">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.employees || 0 }}</div>
              <div class="stat-label">{{ $t('dashboard.totalEmployees') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67C23A;">
              <el-icon><Avatar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.customers || 0 }}</div>
              <div class="stat-label">{{ $t('dashboard.totalCustomers') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #E6A23C;">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.tasks || 0 }}</div>
              <div class="stat-label">{{ $t('dashboard.totalTasks') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #F56C6C;">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.expiringQualifications || 0 }}</div>
              <div class="stat-label">{{ $t('dashboard.expiringQualifications') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第二行：图表 -->
    <el-row :gutter="20" class="mb-20">
      <el-col :span="12" :xs="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ $t('dashboard.taskStatusDistribution') }}</span>
            </div>
          </template>
          <div ref="taskStatusChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12" :xs="24" :md="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ $t('dashboard.monthlyTrend') }}</span>
            </div>
          </template>
          <div ref="monthlyTrendChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 第三行：即将到期的资质提醒列表 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ $t('dashboard.expiringQualificationsList') }}</span>
              <el-button 
                type="primary" 
                size="small" 
                @click="navigateTo('/qualifications')"
              >
                {{ $t('common.viewAll') }}
              </el-button>
            </div>
          </template>
          <el-table 
            :data="expiringQualificationsList" 
            style="width: 100%" 
            max-height="400"
            v-loading="loadingQualifications"
          >
            <el-table-column prop="employee_name" :label="$t('dashboard.employeeName')" width="150" />
            <el-table-column prop="employee_number" :label="$t('dashboard.employeeNumber')" width="120" />
            <el-table-column prop="name" :label="$t('dashboard.trainingName')" min-width="150" />
            <el-table-column prop="category" :label="$t('dashboard.trainingCategory')" width="120">
              <template #default="scope">
                {{ getCategoryName(scope.row.category) }}
              </template>
            </el-table-column>
            <el-table-column prop="expiry_date" :label="$t('dashboard.expiryDate')" width="150">
              <template #default="scope">
                <span :class="getExpiryDateClass(scope.row.expiry_date)">
                  {{ formatDate(scope.row.expiry_date) }}
                </span>
                <div class="days-remaining" v-if="scope.row.days_until_expiry !== undefined">
                  <el-tag 
                    :type="getDaysRemainingTagTypeByDays(scope.row.days_until_expiry)" 
                    size="small"
                  >
                    {{ getDaysRemainingTextByDays(scope.row.days_until_expiry) }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.actions')" width="100" :fixed="isMobile ? false : 'right'">
              <template #default="scope">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="editTrainingRecord(scope.row)"
                >
                  {{ $t('common.edit') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty 
            v-if="!loadingQualifications && expiringQualificationsList.length === 0" 
            :description="$t('dashboard.noExpiringQualifications')" 
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
defineOptions({
  name: 'Dashboard'
})
import { ref, onMounted, nextTick, onBeforeUnmount, watch, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getEmployees, getExpiringTrainingRecords } from '@/api/employees'
import { getCustomers } from '@/api/customers'
import { getTasks } from '@/api/tasks'
import { 
  User, 
  Avatar, 
  Document, 
  Warning
} from '@element-plus/icons-vue'

const router = useRouter()
const { t, locale } = useI18n()
const isMobile = inject('isMobile', ref(false))

const stats = ref({
  employees: 0,
  customers: 0,
  tasks: 0,
  expiringQualifications: 0
})

const expiringQualificationsList = ref([])
const loadingQualifications = ref(false)
const taskStatusChart = ref(null)
const monthlyTrendChart = ref(null)
let taskStatusChartInstance = null
let monthlyTrendChartInstance = null
const latestTasks = ref([])
const latestEmployees = ref([])
const latestCustomers = ref([])

const rerenderCharts = async () => {
  await nextTick()
  renderTaskStatusChart(latestTasks.value)
  renderMonthlyTrendChart(
    latestTasks.value,
    latestEmployees.value,
    latestCustomers.value
  )
}

const loadStats = async () => {
  try {
    const [employees, customers, tasks] = await Promise.all([
      getEmployees().catch(err => {
        console.error('加载员工失败:', err)
        return []
      }),
      getCustomers().catch(err => {
        console.error('加载客户失败:', err)
        return []
      }),
      getTasks().catch(err => {
        console.error('加载任务失败:', err)
        return []
      })
    ])
    
    latestTasks.value = Array.isArray(tasks) ? tasks : []
    latestEmployees.value = Array.isArray(employees) ? employees : []
    latestCustomers.value = Array.isArray(customers) ? customers : []

    stats.value = {
      employees: Array.isArray(employees) ? employees.length : 0,
      customers: Array.isArray(customers) ? customers.length : 0,
      tasks: latestTasks.value.length,
      expiringQualifications: expiringQualificationsList.value.length
    }
    
    // 渲染图表
    await rerenderCharts()
  } catch (error) {
    console.error(t('dashboard.loadStatsFailed'), error)
  }
}

const loadExpiringQualifications = async () => {
  loadingQualifications.value = true
  try {
    const trainingRecords = await getExpiringTrainingRecords()
    
    console.log('即将到期培训记录数据:', trainingRecords)
    
    // API返回的应该是数组，由于axios拦截器已经处理了response.data
    if (Array.isArray(trainingRecords)) {
      if (trainingRecords.length > 0) {
        expiringQualificationsList.value = trainingRecords.slice(0, 10) // 只显示前10条
        // 更新统计数据
        stats.value.expiringQualifications = trainingRecords.length
        console.log('已加载即将到期培训记录:', trainingRecords.length, '条')
      } else {
        expiringQualificationsList.value = []
        stats.value.expiringQualifications = 0
        console.log('暂无即将到期的培训记录')
      }
    } else {
      console.warn('API返回的数据格式不正确:', trainingRecords)
      expiringQualificationsList.value = []
      stats.value.expiringQualifications = 0
    }
  } catch (error) {
    console.error('加载即将到期培训记录失败', error)
    console.error('错误详情:', error.response || error.message)
    expiringQualificationsList.value = []
    stats.value.expiringQualifications = 0
  } finally {
    loadingQualifications.value = false
  }
}

const renderTaskStatusChart = (tasks) => {
  if (!taskStatusChart.value) return
  
  // 销毁旧实例
  if (taskStatusChartInstance) {
    taskStatusChartInstance.dispose()
  }
  
  taskStatusChartInstance = echarts.init(taskStatusChart.value)
  const fontSize = 22
  
  const statusCount = {
    pending: 0,
    completed: 0,
    approved: 0,
    rejected: 0
  }
  
  tasks.forEach(task => {
    const status = task.status || 'pending'
    if (statusCount.hasOwnProperty(status)) {
      statusCount[status]++
    }
  })
  
  const option = {
    textStyle: {
      fontSize
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      textStyle: {
        fontSize
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle',
      textStyle: {
        fontSize
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c} ({d}%)',
          fontSize
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 24,
            fontWeight: 'bold'
          }
        },
        data: [
          { 
            value: statusCount.pending, 
            name: t('dashboard.taskStatus.pending'),
            itemStyle: { color: '#909399' }
          },
          { 
            value: statusCount.completed, 
            name: t('dashboard.taskStatus.completed'),
            itemStyle: { color: '#E6A23C' }
          },
          { 
            value: statusCount.approved, 
            name: t('dashboard.taskStatus.approved'),
            itemStyle: { color: '#67C23A' }
          },
          { 
            value: statusCount.rejected, 
            name: t('dashboard.taskStatus.rejected'),
            itemStyle: { color: '#F56C6C' }
          }
        ]
      }
    ]
  }
  
  taskStatusChartInstance.setOption(option)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    if (taskStatusChartInstance) {
      taskStatusChartInstance.resize()
    }
  })
}

const renderMonthlyTrendChart = (tasks, employees, customers) => {
  if (!monthlyTrendChart.value) return
  
  // 销毁旧实例
  if (monthlyTrendChartInstance) {
    monthlyTrendChartInstance.dispose()
  }
  
  monthlyTrendChartInstance = echarts.init(monthlyTrendChart.value)
  const fontSize = 22
  
  // 计算近6个月的数据
  const months = []
  const taskData = []
  const employeeData = []
  const customerData = []
  
  for (let i = 5; i >= 0; i--) {
    const date = new Date()
    date.setMonth(date.getMonth() - i)
    const monthStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    months.push(monthStr)
    
    const monthStart = new Date(date.getFullYear(), date.getMonth(), 1)
    const monthEnd = new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59)
    
    taskData.push(
      tasks.filter(t => {
        const created = parseItemCreatedDate(t)
        if (!created) return false
        return created >= monthStart && created <= monthEnd
      }).length
    )
    
    employeeData.push(
      employees.filter(e => {
        const created = parseItemCreatedDate(e)
        if (!created) return false
        return created >= monthStart && created <= monthEnd
      }).length
    )
    
    customerData.push(
      customers.filter(c => {
        const created = parseItemCreatedDate(c)
        if (!created) return false
        return created >= monthStart && created <= monthEnd
      }).length
    )
  }
  
  const option = {
    textStyle: {
      fontSize
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      textStyle: {
        fontSize
      }
    },
    legend: {
      data: [
        t('dashboard.tasks'),
        t('dashboard.employees'),
        t('dashboard.customers')
      ],
      bottom: 0,
      textStyle: {
        fontSize
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months,
      axisLabel: {
        fontSize
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize
      }
    },
    series: [
      {
        name: t('dashboard.tasks'),
        type: 'line',
        smooth: true,
        data: taskData,
        itemStyle: { color: '#E6A23C' }
      },
      {
        name: t('dashboard.employees'),
        type: 'line',
        smooth: true,
        data: employeeData,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: t('dashboard.customers'),
        type: 'line',
        smooth: true,
        data: customerData,
        itemStyle: { color: '#67C23A' }
      }
    ]
  }
  
  monthlyTrendChartInstance.setOption(option)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    if (monthlyTrendChartInstance) {
      monthlyTrendChartInstance.resize()
    }
  })
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const getDaysRemaining = (expiryDate) => {
  if (!expiryDate) return null
  const expiry = new Date(expiryDate)
  const now = new Date()
  const diff = expiry - now
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

const getDaysRemainingText = (expiryDate) => {
  const days = getDaysRemaining(expiryDate)
  if (days === null) return ''
  if (days < 0) return t('dashboard.expired')
  if (days === 0) return t('dashboard.expiresToday')
  if (days === 1) return t('dashboard.expiresTomorrow')
  return t('dashboard.daysRemaining', { days })
}

const getDaysRemainingTagType = (expiryDate) => {
  const days = getDaysRemaining(expiryDate)
  if (days === null) return 'info'
  if (days < 0) return 'danger'
  if (days <= 7) return 'warning'
  if (days <= 30) return ''
  return 'success'
}

const getExpiryDateClass = (expiryDate) => {
  const days = getDaysRemaining(expiryDate)
  if (days === null) return ''
  if (days < 0) return 'expired-date'
  if (days <= 7) return 'urgent-date'
  return ''
}

const parseItemCreatedDate = (item) => {
  if (!item) return null
  const raw =
    item.created_at ??
    item.createdAt ??
    item.created_time ??
    item.create_time ??
    item.createdTime ??
    item.createTime
  if (!raw) return null
  if (raw instanceof Date) return raw
  if (typeof raw === 'number') {
    const date = new Date(raw)
    return Number.isNaN(date.getTime()) ? null : date
  }
  if (typeof raw === 'string') {
    const normalized =
      raw.includes(' ') && !raw.includes('T') ? raw.replace(' ', 'T') : raw
    const date = new Date(normalized)
    return Number.isNaN(date.getTime()) ? null : date
  }
  return null
}

// 培训记录专用的函数（使用API返回的days_until_expiry）
const getDaysRemainingTextByDays = (days) => {
  if (days === undefined || days === null) return ''
  if (days < 0) return t('dashboard.expired')
  if (days === 0) return t('dashboard.expiresToday')
  if (days === 1) return t('dashboard.expiresTomorrow')
  return t('dashboard.daysRemaining', { days })
}

const getDaysRemainingTagTypeByDays = (days) => {
  if (days === undefined || days === null) return 'info'
  if (days < 0) return 'danger'
  if (days <= 7) return 'warning'
  if (days <= 30) return ''
  return 'success'
}

const getCategoryName = (category) => {
  if (!category) return '-'
  const categoryMap = {
    'certificate': 'Certificate',
    'first-aid': 'First Aid',
    'manual-handling': 'Manual Handling'
  }
  return categoryMap[category] || category
}

const navigateTo = (path) => {
  router.push(path)
}

const editTrainingRecord = (row) => {
  // 跳转到员工详情页的培训记录部分
  router.push({
    path: `/employees/${row.employee_id}`,
    query: {
      tab: 'training',
      recordId: row.id // 传递培训记录ID，以便后续可以定位到具体记录
    }
  })
}

onMounted(() => {
  loadStats()
  loadExpiringQualifications()
})

watch(
  () => locale.value,
  () => {
    rerenderCharts()
  }
)

onBeforeUnmount(() => {
  if (taskStatusChartInstance) {
    taskStatusChartInstance.dispose()
  }
  if (monthlyTrendChartInstance) {
    monthlyTrendChartInstance.dispose()
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.mb-20 {
  margin-bottom: 20px;
}

.stat-card {
  width: calc(100% - 20px);
  margin: 0 auto;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
}

.stat-card :deep(.el-card__body) {
  padding: 10px;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
  margin-right: 20px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 40px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  font-size: 22px;
  color: #909399;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.days-remaining {
  margin-top: 4px;
}

.expired-date {
  color: #F56C6C;
  font-weight: 600;
}

.urgent-date {
  color: #E6A23C;
  font-weight: 600;
}
</style>
