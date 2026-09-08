<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { useTheme } from './stores/theme'
import { useAuthStore } from './stores/auth'

const { theme, toggle } = useTheme()
const auth = useAuthStore()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
      <div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <RouterLink to="/reservar" class="flex items-center gap-2 font-semibold">
          <span class="grid h-8 w-8 place-items-center rounded-lg bg-brand-500 text-white">A</span>
          <span>AgendaPro <span class="text-brand-500">Simple</span></span>
        </RouterLink>
        <nav class="flex items-center gap-2 text-sm">
          <RouterLink to="/reservar" class="rounded-md px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">Reservar</RouterLink>
          <RouterLink v-if="auth.isAuthenticated" to="/app/dashboard" class="rounded-md px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">Mi panel</RouterLink>
          <RouterLink v-else to="/login" class="rounded-md px-3 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">Ingresar</RouterLink>
          <button class="btn-secondary !px-2" :title="theme === 'dark' ? 'Modo claro' : 'Modo oscuro'" @click="toggle">
            {{ theme === 'dark' ? '☀️' : '🌙' }}
          </button>
        </nav>
      </div>
    </header>

    <main class="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
      <RouterView />
    </main>

    <footer class="border-t border-slate-200 py-4 text-center text-xs text-slate-500 dark:border-slate-800">
      AgendaPro Simple — gestión de turnos mono-usuario
    </footer>
  </div>
</template>
