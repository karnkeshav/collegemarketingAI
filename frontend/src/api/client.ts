import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const statesApi = {
  list: () => api.get('/states').then(r => r.data),
}

export const collegesApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/colleges', { params }).then(r => r.data),
}

export const contactsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/contacts', { params }).then(r => r.data),
  validate: (ids: number[]) =>
    api.post('/contacts/validate', { contact_ids: ids }).then(r => r.data),
  exportUrl: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return `/api/contacts/export${qs}`
  },
  unsubscribe: (id: number) =>
    api.patch(`/contacts/${id}/unsubscribe`).then(r => r.data),
}

export const campaignsApi = {
  list: () => api.get('/campaigns').then(r => r.data),
  get: (id: number) => api.get(`/campaigns/${id}`).then(r => r.data),
  create: (formData: FormData) =>
    api.post('/campaigns', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data),
  send: (id: number, body: { state_codes?: string[]; roles?: string[]; contact_ids?: number[] }) =>
    api.post(`/campaigns/${id}/send`, body).then(r => r.data),
  status: (id: number) => api.get(`/campaigns/${id}/status`).then(r => r.data),
  checkBounces: (id: number) =>
    api.post(`/campaigns/${id}/check-bounces`).then(r => r.data),
  reportExportUrl: (id: number) => `/api/campaigns/${id}/report/export`,
}

export const reportsApi = {
  overview: () => api.get('/reports/overview').then(r => r.data),
  campaignSends: (id: number) =>
    api.get(`/reports/campaigns/${id}/sends`).then(r => r.data),
}

export const scraperApi = {
  start: (state_code?: string, college_id?: number) =>
    api.post('/scrape/start', { state_code, college_id }).then(r => r.data),
  status: () => api.get('/scrape/status').then(r => r.data),
}

export default api
