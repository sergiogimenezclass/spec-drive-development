<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import Alert from '../components/Alert.vue'

const auth = useAuthStore()
const form = ref({ name: '', phone: '', timezone: 'UTC', min_advance_minutes: 60, cancellation_cutoff_hours: 0 })
const pw = ref({ current_password: '', new_password: '', confirm_password: '' })
const error = ref('')
const saved = ref('')
const pwError = ref('')
const pwSaved = ref('')

onMounted(async () => {
  try {
    const u = await auth.fetchProfile()
    form.value = {
      name: u.name,
      phone: u.phone || '',
      timezone: u.timezone,
      min_advance_minutes: u.min_advance_minutes,
      cancellation_cutoff_hours: u.cancellation_cutoff_hours,
    }
  } catch (e) {
    error.value = e.message
  }
})

async function save() {
  error.value = ''
  saved.value = ''
  const cutoff = Number(form.value.cancellation_cutoff_hours)
  if (!Number.isInteger(cutoff) || cutoff < 0) {
    error.value = 'El valor debe ser un número entero mayor o igual a 0.'
    return
  }
  try {
    await api.put('/professional', { ...form.value, cancellation_cutoff_hours: cutoff }, { auth: true })
    await auth.fetchProfile()
    saved.value = 'Perfil actualizado correctamente.'
  } catch (e) {
    error.value = e.details?.[0]?.message || e.message
  }
}

async function changePassword() {
  pwError.value = ''
  pwSaved.value = ''
  if (pw.value.new_password !== pw.value.confirm_password) {
    pwError.value = 'Las contraseñas no coinciden.'
    return
  }
  try {
    await api.put('/professional/password', pw.value, { auth: true })
    pwSaved.value = 'Contraseña cambiada correctamente.'
    pw.value = { current_password: '', new_password: '', confirm_password: '' }
  } catch (e) {
    pwError.value = e.details?.[0]?.message || e.message
  }
}
</script>

<template>
  <div class="max-w-xl space-y-6">
    <h1 class="text-2xl font-bold">Perfil y ajustes</h1>

    <div class="card space-y-3">
      <h2 class="font-semibold">Datos del profesional</h2>
      <Alert v-if="error">{{ error }}</Alert>
      <Alert v-if="saved" type="success">{{ saved }}</Alert>
      <div>
        <label class="label">Nombre</label>
        <input v-model="form.name" class="input" />
      </div>
      <div>
        <label class="label">Email (no editable)</label>
        <input :value="auth.user?.email" class="input" disabled />
      </div>
      <div>
        <label class="label">Teléfono</label>
        <input v-model="form.phone" class="input" />
      </div>
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="label">Zona horaria</label>
          <input v-model="form.timezone" class="input" placeholder="America/..." />
        </div>
        <div>
          <label class="label">Antelación mínima para reservar (min)</label>
          <input v-model.number="form.min_advance_minutes" type="number" min="0" class="input" />
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
        <label class="label font-semibold">Política de Cancelación por Antelación (horas)</label>
        <input v-model.number="form.cancellation_cutoff_hours" type="number" min="0" step="1" class="input" />
        <p class="mt-1 text-xs text-slate-500">
          Horas mínimas antes del turno para que el cliente pueda cancelar o reagendar por su cuenta.
          <span class="font-medium">0 = puede cancelar en cualquier momento hasta el inicio.</span>
        </p>
      </div>

      <button class="btn-primary" @click="save">Guardar cambios</button>
    </div>

    <div class="card space-y-3">
      <h2 class="font-semibold">Cambiar contraseña</h2>
      <Alert v-if="pwError">{{ pwError }}</Alert>
      <Alert v-if="pwSaved" type="success">{{ pwSaved }}</Alert>
      <div>
        <label class="label">Contraseña actual</label>
        <input v-model="pw.current_password" type="password" class="input" />
      </div>
      <div>
        <label class="label">Nueva contraseña</label>
        <input v-model="pw.new_password" type="password" class="input" />
      </div>
      <div>
        <label class="label">Confirmar nueva</label>
        <input v-model="pw.confirm_password" type="password" class="input" />
      </div>
      <button class="btn-primary" @click="changePassword">Cambiar contraseña</button>
    </div>
  </div>
</template>
