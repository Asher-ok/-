import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/sign/document/:token',
    name: 'SignDocument',
    component: () => import('@/views/sign/SignDocument.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/sign/employee-contract/:token',
    name: 'SignEmployeeContract',
    component: () => import('@/views/sign/SignDocument.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'employees',
        name: 'Employees',
        component: () => import('@/views/employees/EmployeeList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'employees/:id',
        name: 'EmployeeDetail',
        component: () => import('@/views/employees/EmployeeDetail.vue')
      },
      {
        path: 'customers',
        name: 'Customers',
        redirect: '/customers/built'
      },
      {
        path: 'customers/built',
        name: 'CustomersBuilt',
        component: () => import('@/views/customers/CustomerList.vue'),
        meta: { keepAlive: true, customerStatus: '已建档' }
      },
      {
        path: 'customers/not-built',
        name: 'CustomersNotBuilt',
        component: () => import('@/views/customers/CustomerList.vue'),
        meta: { keepAlive: true, customerStatus: '未建档' }
      },
      {
        path: 'customers/pending',
        name: 'CustomersPending',
        component: () => import('@/views/customers/CustomerList.vue'),
        meta: { keepAlive: true, customerStatus: '待建档' }
      },
      {
        path: 'customers/:id',
        name: 'CustomerDetail',
        component: () => import('@/views/customers/CustomerDetail.vue')
      },
      {
        path: 'tasks',
        name: 'Tasks',
        redirect: '/tasks/all'
      },
      {
        path: 'tasks/all',
        name: 'TasksAll',
        component: () => import('@/views/tasks/TaskList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'tasks/issued',
        name: 'TasksIssued',
        component: () => import('@/views/invoices/InvoiceList.vue'),
        meta: { keepAlive: true, invoiceTab: 'issued' }
      },
      {
        path: 'tasks/unissued',
        name: 'TasksUnissued',
        component: () => import('@/views/invoices/InvoiceList.vue'),
        meta: { keepAlive: true, invoiceTab: 'unissued' }
      },
      {
        path: 'tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/views/tasks/TaskDetail.vue')
      },
      {
        path: 'questionnaires',
        name: 'Questionnaires',
        redirect: '/questionnaires/templates'
      },
      {
        path: 'questionnaires/templates',
        name: 'QuestionnaireTemplates',
        component: () => import('@/views/questionnaires/QuestionnaireList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'questionnaires/submissions',
        name: 'QuestionnaireSubmissions',
        component: () => import('@/views/questionnaires/QuestionnaireSubmissions.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'questionnaires/:id',
        name: 'QuestionnaireDetail',
        component: () => import('@/views/questionnaires/QuestionnaireDetail.vue')
      },
      {
        path: 'qualifications',
        name: 'Qualifications',
        component: () => import('@/views/qualifications/QualificationList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'invoices',
        name: 'Invoices',
        redirect: '/tasks/issued'
      },
      {
        path: 'invoices-unissued',
        name: 'UnissuedInvoices',
        redirect: '/tasks/unissued'
      },
      {
        path: 'invoices/:id',
        name: 'InvoiceDetail',
        component: () => import('@/views/invoices/InvoiceDetail.vue')
      },
      {
        path: 'invoice-services',
        name: 'InvoiceServices',
        component: () => import('@/views/invoices/InvoiceList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'leave-requests',
        name: 'LeaveRequests',
        component: () => import('@/views/leave/LeaveRequestList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'template-files',
        name: 'TemplateFiles',
        component: () => import('@/views/templateFiles/TemplateFileList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'incident-templates/templates',
        name: 'IncidentTemplates',
        component: () => import('@/views/incidentTemplates/IncidentTemplateList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'incident-templates/templates/:id',
        name: 'IncidentTemplateDetail',
        component: () => import('@/views/incidentTemplates/IncidentTemplateDetail.vue')
      },
      {
        path: 'incident-templates/submissions',
        name: 'IncidentTemplateSubmissions',
        component: () => import('@/views/incidentTemplates/IncidentTemplateSubmissions.vue')
      },
      {
        path: 'task-record-templates/templates',
        name: 'TaskRecordTemplates',
        component: () => import('@/views/taskRecordTemplates/TaskRecordTemplateList.vue'),
        meta: { keepAlive: true }
      },
      {
        path: 'task-record-templates/templates/:id',
        name: 'TaskRecordTemplateDetail',
        component: () => import('@/views/taskRecordTemplates/TaskRecordTemplateDetail.vue')
      },
      {
        path: 'task-record-templates/submissions',
        name: 'TaskRecordTemplateSubmissions',
        component: () => import('@/views/taskRecordTemplates/TaskRecordTemplateSubmissions.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach((to, from, next) => {
  // 快速检查 token，避免不必要的计算
  const token = localStorage.getItem('token')
  const isAuthenticated = !!token
  
  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
