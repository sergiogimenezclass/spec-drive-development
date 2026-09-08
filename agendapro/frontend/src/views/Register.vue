<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Alert from '../components/Alert.vue'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ name: '', email: '', password: '', confirm_password: '' })
const error = ref('')
const fieldErrors = ref({})
const loading = ref(false)

async function submit() {
  error.value = ''
  fieldErrors.value = {}
  if (form.value.password !== form.value.confirm_password) {
    fieldErrors.value = { confirm_password: 'Las contraseñas no coinciden.' }
    return
  }
  loading.value = true
  try {
    await auth.register(form.value)
    router.push({ name: 'dashboard' })
  } catch (e) {
    if (e.details && e.details.length) {
      const map = {}
      e.details.forEach((d) => (map[d.field] = d.message))
      fieldErrors.value = map
    }
    error.value = e.message || 'No se pudo completar el registro.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-sm">
    <div class="card">
      <h1 class="mb-1 text-xl font-semibold">Crear cuenta</h1>
      <p class="mb-4 text-sm text-slate-500">
        Solo puede existir un profesional por instancia.
      </p>
      <Alert v-if="error">{{ error }}</Alert>
      <form class="mt-4 space-y-4" @submit.prevent="submit">
        <div>
          <label class="label">Nombre completo</label>
          <input v-model="form.name" class="input" required />
          <p v-if="fieldErrors.name" class="mt-1 text-xs text-red-600">{{ fieldErrors.name }}</p>
        </div>
        <div>
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" required />
          <p v-if="fieldErrors.email" class="mt-1 text-xs text-red-600">{{ fieldErrors.email }}</p>
        </div>
        <div>
          <label class="label">Contraseña</label>
          <input v-model="form.password" type="password" class="input" required />
          <p class="mt-1 text-xs text-slate-400">Mín. 8 caracteres, una mayúscula, una minúscula y un número.</p>
          <p v-if="fieldErrors.password" class="mt-1 text-xs text-red-600">{{ fieldErrors.password }}</p>
        </div>
        <div>
          <label class="label">Confirmar contraseña</label>
          <input v-model="form.confirm_password" type="password" class="input" required />
          <p v-if="fieldErrors.confirm_password" class="mt-1 text-xs text-red-600">{{ fieldErrors.confirm_password }}</p>
        </div>
        <button class="btn-primary w-full" :disabled="loading">{{ loading ? 'Creando…' : 'Registrarme' }}</button>
      </form>
      <p class="mt-4 text-center text-sm text-slate-500">
        ¿Ya tenés cuenta?
        <RouterLink to="/login" class="text-brand-500 hover:underline">Ingresá</RouterLink>
      </p>
    </div>
  </div>
</template>
