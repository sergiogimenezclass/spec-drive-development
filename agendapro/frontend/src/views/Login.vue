<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Alert from '../components/Alert.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// Credenciales por defecto para pruebas de desarrollo
const email = ref('pro@example.com')
const password = ref('Passw0rd123')
const error = ref('')
const loading = ref(false)

function fillDemo() {
  email.value = 'pro@example.com'
  password.value = 'Passw0rd123'
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push(route.query.next || { name: 'dashboard' })
  } catch (e) {
    error.value = e.message || 'No se pudo iniciar sesión.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-sm">
    <div class="card">
      <h1 class="mb-1 text-xl font-semibold">Iniciar sesión</h1>
      <p class="mb-4 text-sm text-slate-500">Panel del profesional</p>
      
      <!-- Aviso de Modo Prueba -->
      <div class="mb-4 flex items-center justify-between rounded bg-amber-50 p-2.5 text-xs text-amber-800 border border-amber-200">
        <span>⚡ Modo Prueba Activo</span>
        <button type="button" @click="fillDemo" class="font-semibold underline hover:text-amber-950">Rellenar Credenciales</button>
      </div>

      <Alert v-if="error">{{ error }}</Alert>
      <form class="mt-4 space-y-4" @submit.prevent="submit">
        <div>
          <label class="label">Email</label>
          <input v-model="email" type="email" class="input" required autocomplete="email" />
        </div>
        <div>
          <label class="label">Contraseña</label>
          <input v-model="password" type="password" class="input" required autocomplete="current-password" />
        </div>
        <button class="btn-primary w-full" :disabled="loading">{{ loading ? 'Ingresando…' : 'Ingresar' }}</button>
      </form>
      <p class="mt-4 text-center text-sm text-slate-500">
        ¿No tenés cuenta?
        <RouterLink to="/register" class="text-brand-500 hover:underline">Registrate</RouterLink>
      </p>
    </div>
  </div>
</template>
