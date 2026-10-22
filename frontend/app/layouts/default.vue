<template>
  <div class="flex h-dvh bg-gray-50 overflow-hidden">
    <!-- Fondo oscuro cuando el menú está abierto en pantallas chicas -->
    <Transition name="fade">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 z-30 bg-slate-900/50 lg:hidden"
        @click="sidebarOpen = false"
      />
    </Transition>

    <AppSidebar />
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <AppHeader />
      <main class="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 scrollbar-thin">
        <div class="mx-auto w-full max-w-[1600px]">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
const sidebarOpen = useState<boolean>("sidebar-open", () => false);
const route = useRoute();

// Al navegar, cerrar el menú (en móvil)
watch(() => route.fullPath, () => { sidebarOpen.value = false; });
</script>

<style>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
