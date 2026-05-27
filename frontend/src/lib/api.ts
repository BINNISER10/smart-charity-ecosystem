import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

// ── Dashboard ────────────────────────────────────────────────────────────────
export const getDashboard = () => api.get('/dashboard').then(r => r.data)

// ── Beneficiaries ─────────────────────────────────────────────────────────────
export const getBeneficiaries = (search = '', includeArchived = false) =>
  api.get('/beneficiaries', { params: { search, include_archived: includeArchived } }).then(r => r.data)

export const createBeneficiary = (data: any) =>
  api.post('/beneficiaries', data).then(r => r.data)

export const getBeneficiaryDetail = (id: string) =>
  api.get(`/beneficiaries/${id}`).then(r => r.data)

export const archiveBeneficiary = (id: string) =>
  api.post(`/beneficiaries/${id}/archive`).then(r => r.data)

export const restoreBeneficiary = (id: string) =>
  api.post(`/beneficiaries/${id}/restore`).then(r => r.data)

// ── Applications ──────────────────────────────────────────────────────────────
export const getApplications = (params?: { status?: string; sector?: string }) =>
  api.get('/applications', { params }).then(r => r.data)

export const createApplication = (data: any) =>
  api.post('/applications', data).then(r => r.data)

export const approveApplication = (id: string, data: any) =>
  api.post(`/applications/${id}/approve`, data).then(r => r.data)

export const rejectApplication = (id: string, data: any) =>
  api.post(`/applications/${id}/reject`, data).then(r => r.data)

export const cancelApplication = (id: string, data: any) =>
  api.post(`/applications/${id}/cancel`, data).then(r => r.data)

export const disburseApplication = (id: string, executorId = 'API-ADMIN') =>
  api.post(`/applications/${id}/disburse`, { executor_id: executorId }).then(r => r.data)

export const updateBeneficiary = (id: string, data: any) =>
  api.patch(`/beneficiaries/${id}`, data).then(r => r.data)

export const updateApplication = (id: string, data: any) =>
  api.patch(`/applications/${id}`, data).then(r => r.data)

// ── Finance ───────────────────────────────────────────────────────────────────
export const getFinanceReport = () => api.get('/finance/report').then(r => r.data)

export const getTransactions = (params?: {
  fund_type?: string; limit?: number; from_date?: string; to_date?: string
}) => api.get('/finance/transactions', { params }).then(r => r.data)

export const donate = (data: any) =>
  api.post('/finance/donate', data).then(r => r.data)

// ── Sectors ───────────────────────────────────────────────────────────────────
export const getSectors = () => api.get('/sectors').then(r => r.data)

// ── Audit & Alerts ────────────────────────────────────────────────────────────
export const getAuditLog  = (limit = 50) => api.get('/audit-log', { params: { limit } }).then(r => r.data)
export const getAlerts    = () => api.get('/alerts').then(r => r.data)

// ── Zakat ─────────────────────────────────────────────────────────────────────
export const calculateZakat = (data: any) =>
  api.post('/zakat/calculate', data).then(r => r.data)

// ── Donors ────────────────────────────────────────────────────────────────────
export const getDonors = (search = '') =>
  api.get('/finance/donors', { params: { search } }).then(r => r.data)

// ── AI Predictions ────────────────────────────────────────────────────────────
export const getAIPredictions = () => api.get('/ai/predictions').then(r => r.data)

// ── Policies ──────────────────────────────────────────────────────────────────
export const getPolicies        = () => api.get('/policies').then(r => r.data)
export const getConfigRules     = () => api.get('/config/rules').then(r => r.data)
export const getConfigStructure = () => api.get('/config/structure').then(r => r.data)

// ── Export ────────────────────────────────────────────────────────────────────
export const exportExcelUrl  = '/api/export/excel'
export const exportReportUrl = '/api/export/report'

// ── Helpers ───────────────────────────────────────────────────────────────────
export const getEnums   = () => api.get('/enums').then(r => r.data)
export const getUsers   = () => api.get('/users').then(r => r.data)
export const saveData   = () => api.post('/data/save').then(r => r.data)
export const todayHijri = () => api.get('/hijri/today').then(r => r.data)
