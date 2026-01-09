<template>
  <aside class="w-64 bg-surface border-r border-slate-200 flex flex-col justify-between h-full shrink-0 z-20">
    <div class="flex flex-col p-4 gap-6">
      <!-- App Header -->
      <div class="flex flex-col px-2">
        <div class="flex items-center gap-2 mb-1">
          <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white">
            <span class="material-symbols-outlined text-[20px]">smart_display</span>
          </div>
          <h1 class="text-slate-900 text-base font-bold leading-none tracking-tight">
            VideoSearch AI
          </h1>
        </div>
        <p class="text-slate-500 text-xs font-medium pl-10">
          Local v1.0.4
        </p>
      </div>

      <!-- Navigation -->
      <nav class="flex flex-col gap-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          v-slot="{ isActive }"
          custom
        >
          <a
            :href="item.path"
            :class="[
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
              isActive
                ? 'bg-primary/10 text-primary font-semibold'
                : 'text-slate-600 hover:bg-slate-50 font-medium'
            ]"
            @click.prevent="navigateTo(item.path)"
          >
            <span
              class="material-symbols-outlined text-[22px] transition-colors"
              :class="[
                isActive ? 'fill-1' : 'group-hover:text-primary'
              ]"
            >
              {{ item.icon }}
            </span>
            <span>{{ item.label }}</span>
          </a>
        </router-link>
      </nav>
    </div>

    <!-- Footer / Status -->
    <StatusIndicator />
  </aside>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import StatusIndicator from './StatusIndicator.vue'

interface NavItem {
  path: string
  label: string
  icon: string
}

const router = useRouter()

const navItems: NavItem[] = [
  {
    path: '/library',
    label: 'Library',
    icon: 'video_library'
  },
  {
    path: '/search',
    label: 'Search',
    icon: 'search'
  },
  {
    path: '/chat',
    label: 'Chat',
    icon: 'chat'
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: 'settings'
  }
]

const navigateTo = (path: string) => {
  router.push(path)
}
</script>
