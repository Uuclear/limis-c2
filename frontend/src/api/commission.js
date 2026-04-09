import request from './request'

export function listCommissions(params) {
  return request.get('/commissions', { params })
}

export function getCommission(id) {
  return request.get(`/commissions/${id}`)
}

export function createCommission(data) {
  return request.post('/commissions', data)
}

export function updateCommission(id, data) {
  return request.put(`/commissions/${id}`, data)
}

export function submitCommission(id) {
  return request.post(`/commissions/${id}/submit`)
}

export function reviewCommission(id, data) {
  return request.post(`/commissions/${id}/review`, data)
}

export function deleteCommission(id) {
  return request.delete(`/commissions/${id}`)
}

export function listNumberingRules() {
  return request.get('/numbering-rules')
}

export function updateNumberingRule(id, data) {
  return request.put(`/numbering-rules/${id}`, data)
}
