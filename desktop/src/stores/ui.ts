import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // State
  const darkMode = ref(false)
  const sidebarCollapsed = ref(false)
  const showUnsavedChangesDialog = ref(false)
  const activeSection = ref<string | null>(null)

  // Computed
  const theme = computed(() => (darkMode.value ? 'dark' : 'light'))

  // Actions
  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    applyDarkMode()
    saveDarkModePreference()
  }

  function setDarkMode(value: boolean) {
    darkMode.value = value
    applyDarkMode()
    saveDarkModePreference()
  }

  function initializeDarkMode() {
    // Check localStorage first
    const savedDarkMode = localStorage.getItem('darkMode')

    if (savedDarkMode !== null) {
      darkMode.value = savedDarkMode === 'true'
    } else {
      // Fall back to system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      darkMode.value = prefersDark
    }

    applyDarkMode()
  }

  function applyDarkMode() {
    if (darkMode.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function saveDarkModePreference() {
    localStorage.setItem('darkMode', darkMode.value.toString())
  }

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

  // Watch for system dark mode changes
  function watchSystemDarkMode() {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')

    darkModeQuery.addEventListener('change', (e) => {
      // Only update if user hasn't set a preference
      const savedDarkMode = localStorage.getItem('darkMode')
      if (savedDarkMode === null) {
        darkMode.value = e.matches
        applyDarkMode()
      }
    })
  }

  // Initialize watchers
  function initialize() {
    initializeDarkMode()
    initializeSidebarState()
    watchSystemDarkMode()
  }

  return {
    // State
    darkMode,
    sidebarCollapsed,
    showUnsavedChangesDialog,
    activeSection,

    // Computed
    theme,

    // Actions
    toggleDarkMode,
    setDarkMode,
    initializeDarkMode,
    toggleSidebar,
    setSidebarCollapsed,
    setActiveSection,
    scrollToSection,
    openUnsavedChangesDialog,
    closeUnsavedChangesDialog,
    initialize
  }
})
