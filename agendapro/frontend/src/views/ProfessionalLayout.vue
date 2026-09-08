<script setup>
import { onMounted } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

onMounted(() => {
  auth.fetchProfile().catch(() => {})
})

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="grid gap-6 md:grid-cols-[200px_1fr]">
    <aside class="space-y-1">
      <div class="mb-3 px-2 text-sm text-slate-500">
        Hola, <span class="font-medium text-slate-700 dark:text-slate-200">{{ auth.user?.name || 'Profesional' }}</span>
      </div>
      <RouterLink to="/app/dashboard" class="block rounded-lg px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800" active-class="bg-brand-50 text-brand-700 font-medium dark:bg-brand-700/20 dark:text-brand-100">Turnos</RouterLink>
      <RouterLink to="/app/services" class="block rounded-lg px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800" active-class="bg-brand-50 text-brand-700 font-medium dark:bg-brand-700/20 dark:text-brand-100">Servicios</RouterLink>
      <RouterLink to="/app/availability" class="block rounded-lg px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800" active-class="bg-brand-50 text-brand-700 font-medium dark:bg-brand-700/20 dark:text-brand-100">Disponibilidad</RouterLink>
      <RouterLink to="/app/profile" class="block rounded-lg px-3 py-2 text-sm hover:bg-slate-100 dark:hover:bg-slate-800" active-class="bg-brand-50 text-brand-700 font-medium dark:bg-brand-700/20 dark:text-brand-100">Configuración</RouterLink>
      <button class="mt-2 block w-full rounded-lg px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950" @click="logout">Cerrar sesión</button>
    </aside>
    <section>
      <RouterView />
    </section>
  </div>
</template>
