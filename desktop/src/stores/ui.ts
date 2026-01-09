import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // State
  const sidebarCollapsed = ref(false)
  const showUnsavedChangesDialog = ref(false)
  const activeSection = ref<string | null>(null)

  // Actions
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    saveSidebarPreference()
  }

  function setSidebarCollapsed(value: boolean) {
    sidebarCollapsed.value = value
    saveSidebarPreference()
  }

  function saveSidebarPreference() {
    localStorage.setItem('sidebarCollapsed', sidebarCollapsed.value.toString())
  }

  function initializeSidebarState() {
    const savedState = localStorage.getItem('sidebarCollapsed')
    if (savedState !== null) {
      sidebarCollapsed.value = savedState === 'true'
    }
  }

  function setActiveSection(section: string | null) {
    activeSection.value = section
  }

  function scrollToSection(sectionId: string) {
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setActiveSection(sectionId)
    }
  }

  function openUnsavedChangesDialog() {
    showUnsavedChangesDialog.value = true
  }

  function closeUnsavedChangesDialog() {
    showUnsavedChangesDialog.value = false
  }

  // Initialize
  function initialize() {
    initializeSidebarState()
  }

  return {
    // State
    sidebarCollapsed,
    showUnsavedChangesDialog,
    activeSection,

    // Actions
    toggleSidebar,
    setSidebarCollapsed,
    setActiveSection,
    scrollToSection,
    openUnsavedChangesDialog,
    closeUnsavedChangesDialog,
    initialize
  }
})
