import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const currentProjectId = ref(null)
  const currentProjectName = ref('')

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setCurrentProject(id, name) {
    currentProjectId.value = id
    currentProjectName.value = name
  }

  return {
    sidebarCollapsed, currentProjectId, currentProjectName,
    toggleSidebar, setCurrentProject,
  }
})
