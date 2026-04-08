import request from './request'

// --- Project (工程) ---
export function listProjects(params) {
  return request.get('/projects', { params })
}

export function getProject(id) {
  return request.get(`/projects/${id}`)
}

export function createProject(data) {
  return request.post('/projects', data)
}

export function updateProject(id, data) {
  return request.put(`/projects/${id}`, data)
}

export function deleteProject(id) {
  return request.delete(`/projects/${id}`)
}

// --- UnitProject (单位工程) ---
export function createUnitProject(data) {
  return request.post('/unit-projects', data)
}

export function updateUnitProject(id, data) {
  return request.put(`/unit-projects/${id}`, data)
}

export function deleteUnitProject(id) {
  return request.delete(`/unit-projects/${id}`)
}

// --- Division (分部工程) ---
export function createDivision(data) {
  return request.post('/divisions', data)
}

export function updateDivision(id, data) {
  return request.put(`/divisions/${id}`, data)
}

export function deleteDivision(id) {
  return request.delete(`/divisions/${id}`)
}

// --- SubItem (分项工程) ---
export function createSubItem(data) {
  return request.post('/sub-items', data)
}

export function updateSubItem(id, data) {
  return request.put(`/sub-items/${id}`, data)
}

export function deleteSubItem(id) {
  return request.delete(`/sub-items/${id}`)
}
