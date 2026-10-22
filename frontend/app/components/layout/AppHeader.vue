<template>
  <header class="h-14 bg-white border-b border-gray-100 px-4 sm:px-6 flex items-center justify-between gap-3 shrink-0">
    <div class="flex items-center gap-3 min-w-0">
      <!-- Botón del menú (solo en pantallas chicas) -->
      <button
        type="button"
        class="lg:hidden -ml-1 p-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors"
        aria-label="Abrir menú"
        @click="sidebarOpen = !sidebarOpen"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <span class="font-semibold text-gray-800 truncate text-sm sm:text-base">{{ pageTitle }}</span>
    </div>
    <div class="flex items-center gap-3 shrink-0">
      <span class="text-xs text-gray-400 hidden xl:block">{{ today }}</span>
      <div class="w-px h-4 bg-gray-200 hidden xl:block" />
      <div class="flex items-center gap-2">
        <div class="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold">
          {{ initials }}
        </div>
        <span class="text-xs font-medium text-gray-700 hidden md:block max-w-[160px] truncate">{{ auth.fullName }}</span>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'
const route = useRoute()
const auth  = useAuthStore()
const sidebarOpen = useState<boolean>('sidebar-open', () => false)
const pageTitle = computed(() => String(route.meta.title ?? 'PeleAnálise'))
const today = new Intl.DateTimeFormat('es-MX', { dateStyle: 'long' }).format(new Date())
const initials = computed(() => {
  const u = auth.user
  if (!u) return '?'
  return `${u.firstName[0]}${u.lastName[0]}`.toUpperCase()
})
</script>
