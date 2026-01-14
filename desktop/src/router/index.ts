import { createRouter, createWebHistory } from 'vue-router'
import LibraryView from '@/views/LibraryView.vue'
import SearchView from '@/views/SearchView.vue'
import ChatView from '@/views/ChatView.vue'
import SettingsView from '@/views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/search'
    },
    {
      path: '/library',
      name: 'library',
      component: LibraryView
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView
    }
  ]
})

export default router
