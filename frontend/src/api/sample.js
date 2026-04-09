import request from './request'

export function listSamples(params) {
  return request.get('/samples', { params })
}

export function getSample(id) {
  return request.get(`/samples/${id}`)
}

export function createSample(data) {
  return request.post('/samples', data)
}

export function updateSample(id, data) {
  return request.put(`/samples/${id}`, data)
}

export function receiveSample(id, data) {
  return request.post(`/samples/${id}/receive`, data)
}

export function updateSampleStatus(id, data) {
  return request.post(`/samples/${id}/status`, data)
}
