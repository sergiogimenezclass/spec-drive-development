<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import Alert from '../components/Alert.vue'
import { WEEKDAYS, formatDateTime } from '../utils/format'

const weekly = ref(WEEKDAYS.map((w) => ({ ...w, enabled: false, start_time: '09:00', end_time: '17:00' })))
const blocked = ref([])
const error = ref('')
const saved = ref('')
const loading = ref(true)

const blockForm = ref({ start_time: '', end_time: '', reason: '' })

onMounted(load)

async function load() {
  loading.value = true
  try {
    const data = await api.get('/professional/availability', { auth: true })
    const map = {}
    data.weekly_hours.forEach((w) => (map[w.day_of_week] = w))
    weekly.value = weekly.value.map((w) =>
      map[w.value] ? { ...w, enabled: true, start_time: map[w.value].start_time, end_time: map[w.value].end_time } : w
    )
    blocked.value = data.blocked_slots
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function saveWeekly() {
  error.value = ''
  saved.value = ''
  const payload = weekly.value
    .filter((w) => w.enabled)
    .map((w) => ({ day_of_week: w.value, start_time: w.start_time, end_time: w.end_time }))
  try {
    await api.put('/professional/availability/weekly-hours', payload, { auth: true })
    saved.value = 'Horario semanal guardado.'
  } catch (e) {
    error.value = e.message
  }
}

function toZ(localValue) {
  if (!localValue) return null
  return localValue.length === 16 ? localValue + ':00Z' : localValue + 'Z'
}

async function addBlock() {
  error.value = ''
  if (!blockForm.value.start_time || !blockForm.value.end_time) {
    error.value = 'Indicá inicio y fin del bloqueo.'
    return
  }
  try {
    const created = await api.post(
      '/professional/availability/blocked-slots',
      {
        start_time: toZ(blockForm.value.start_time),
        end_time: toZ(blockForm.value.end_time),
        reason: blockForm.value.reason || null,
      },
      { auth: true }
    )
    blocked.value.push(created)
    blockForm.value = { start_time: '', end_time: '', reason: '' }
  } catch (e) {
    error.value = e.message
  }
}

async function removeBlock(b) {
  try {
    await api.del(`/professional/availability/blocked-slots/${b.id}`, { auth: true })
    blocked.value = blocked.value.filter((x) => x.id !== b.id)
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Disponibilidad</h1>
      <p class="text-sm text-slate-500">Definí tus horarios de trabajo y tus bloqueos.</p>
    </div>

    <Alert v-if="error">{{ error }}</Alert>
    <Alert v-if="saved" type="success">{{ saved }}</Alert>

    <div class="card">
      <h2 class="mb-3 font-semibold">Horario semanal</h2>
      <div class="space-y-2">
        <div v-for="w in weekly" :key="w.value" class="flex items-center gap-3">
          <label class="flex w-32 items-center gap-2 text-sm">
            <input v-model="w.enabled" type="checkbox" class="h-4 w-4 rounded" />
            {{ w.label }}
          </label>
          <template v-if="w.enabled">
            <input v-model="w.start_time" type="time" class="input !w-32" />
            <span class="text-slate-400">a</span>
            <input v-model="w.end_time" type="time" class="input !w-32" />
          </template>
          <span v-else class="text-sm text-slate-400">No disponible</span>
        </div>
      </div>
      <button class="btn-primary mt-4" @click="saveWeekly">Guardar horario</button>
    </div>

    <div class="card">
      <h2 class="mb-3 font-semibold">Bloqueos (vacaciones, feriados, pausas)</h2>
      <div class="grid gap-3 sm:grid-cols-4">
        <div>
          <label class="label">Inicio</label>
          <input v-model="blockForm.start_time" type="datetime-local" class="input" />
        </div>
        <div>
          <label class="label">Fin</label>
          <input v-model="blockForm.end_time" type="datetime-local" class="input" />
        </div>
        <div>
          <label class="label">Motivo</label>
          <input v-model="blockForm.reason" class="input" placeholder="Ej: Almuerzo" />
        </div>
        <div class="flex items-end">
          <button class="btn-primary w-full" @click="addBlock">Agregar</button>
        </div>
      </div>
      <p class="mt-2 text-xs text-slate-400">Las horas se interpretan en UTC (zona del servidor).</p>

      <div v-if="!blocked.length" class="mt-4 text-sm text-slate-500">No hay bloqueos.</div>
      <div v-else class="mt-4 space-y-2">
        <div v-for="b in blocked" :key="b.id" class="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm dark:border-slate-700">
          <div>
            <span class="font-medium">{{ b.reason || 'Bloqueo' }}</span>
            <span class="text-slate-500"> · {{ formatDateTime(b.start_time) }} → {{ formatDateTime(b.end_time) }}</span>
          </div>
          <button class="btn-danger !py-1 !px-2 text-xs" @click="removeBlock(b)">Quitar</button>
        </div>
      </div>
    </div>
  </div>
</template>
