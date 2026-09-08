<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from '../api/client'
import Alert from '../components/Alert.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { formatDateTime, formatTime, todayISODate, addDaysISODate } from '../utils/format'

const date = ref(todayISODate())
const appts = ref([])
const loading = ref(false)
const error = ref('')
const rescheduling = ref(null) // appointment id en proceso
const dateOptions = ref([])
const slots = ref([])
const newSlot = ref(null)

onMounted(load)
watch(date, load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    appts.value = await api.get('/professional/appointments', { auth: true, query: { date: date.value } })
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function setStatus(appt, status) {
  error.value = ''
  try {
    const updated = await api.put(`/professional/appointments/${appt.id}/status`, { status }, { auth: true })
    Object.assign(appt, updated)
  } catch (e) {
    error.value = e.message
  }
}

async function openReschedule(appt) {
  rescheduling.value = appt.id
  newSlot.value = null
  slots.value = []
  const base = todayISODate()
  dateOptions.value = Array.from({ length: 21 }, (_, i) => {
    const iso = addDaysISODate(base, i)
    const d = new Date(iso + 'T00:00:00')
    return { iso, label: d.toLocaleDateString('es', { weekday: 'short', day: 'numeric', month: 'short' }) }
  })
}

async function pickDate(iso) {
  newSlot.value = null
  const appt = appts.value.find((a) => a.id === rescheduling.value)
  slots.value = await api.get(`/public/available-slots?serviceId=${appt.service_id}&date=${iso}`)
}

async function doReschedule(appt) {
  error.value = ''
  try {
    const updated = await api.put(
      `/professional/appointments/${appt.id}/reschedule`,
      { new_start_time: newSlot.value.start_time },
      { auth: true }
    )
    Object.assign(appt, updated)
    rescheduling.value = null
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Turnos</h1>
      <input v-model="date" type="date" class="input !w-auto" />
    </div>

    <Alert v-if="error">{{ error }}</Alert>

    <div v-if="loading" class="text-sm text-slate-500">Cargando…</div>
    <div v-else-if="!appts.length" class="card text-sm text-slate-500">No hay turnos este día.</div>

    <div v-else class="space-y-3">
      <div v-for="a in appts" :key="a.id" class="card">
        <div class="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div class="font-semibold">{{ a.service_name }}</div>
            <div class="text-sm text-slate-500">{{ formatDateTime(a.start_time) }} · {{ a.client_name }}</div>
            <div class="text-xs text-slate-400">{{ a.client_email }} {{ a.client_phone ? '· ' + a.client_phone : '' }}</div>
            <div v-if="a.notes" class="mt-1 text-xs text-slate-500">Nota: {{ a.notes }}</div>
          </div>
          <StatusBadge :status="a.status" />
        </div>

        <div v-if="a.status === 'BOOKED'" class="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3 dark:border-slate-800">
          <button class="btn-secondary" @click="setStatus(a, 'COMPLETED')">Completar</button>
          <button class="btn-secondary" @click="setStatus(a, 'NO_SHOW')">No presentó</button>
          <button class="btn-secondary" @click="openReschedule(a)">Reagendar</button>
          <button class="btn-danger" @click="setStatus(a, 'CANCELLED')">Cancelar</button>
        </div>

        <div v-if="rescheduling === a.id" class="mt-3 space-y-2 rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="d in dateOptions"
              :key="d.iso"
              class="rounded-full border px-2 py-0.5 text-xs capitalize"
              :class="slots.length && newSlot === null ? 'border-slate-200 dark:border-slate-700' : 'border-slate-200 dark:border-slate-700'"
              @click="pickDate(d.iso)"
            >
              {{ d.label }}
            </button>
          </div>
          <div v-if="slots.length" class="grid grid-cols-4 gap-2">
            <button
              v-for="s in slots"
              :key="s.start_time"
              class="rounded-lg border px-2 py-1 text-sm"
              :class="newSlot?.start_time === s.start_time ? 'border-brand-500 bg-brand-50 dark:bg-brand-700/20' : 'border-slate-200 dark:border-slate-700'"
              @click="newSlot = s"
            >
              {{ formatTime(s.start_time) }}
            </button>
          </div>
          <div class="flex gap-2">
            <button class="btn-primary" :disabled="!newSlot" @click="doReschedule(a)">Guardar nuevo horario</button>
            <button class="btn-secondary" @click="rescheduling = null">Cancelar</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
