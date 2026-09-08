<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/client'
import Alert from '../components/Alert.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { formatDateTime, formatTime, todayISODate, addDaysISODate } from '../utils/format'

const props = defineProps({ token: String })

const appt = ref(null)
const error = ref('')
const message = ref('')
const loading = ref(true)
const busy = ref(false)

const rescheduling = ref(false)
const dateOptions = ref([])
const selectedDate = ref(null)
const slots = ref([])
const newSlot = ref(null)

const sm = computed(() => appt.value?.self_management || {})
const canManage = computed(() => appt.value?.status === 'BOOKED' && sm.value.can_cancel)
const blockedReason = computed(() => {
  if (appt.value?.status !== 'BOOKED' || sm.value.can_cancel) return ''
  if (sm.value.started) {
    return 'Este turno ya comenzó o finalizó y no puede gestionarse en línea. Contactá al profesional.'
  }
  const n = sm.value.cancellation_cutoff_hours
  return `El plazo para cancelar o reagendar en línea venció (se permite con al menos ${n} h de anticipación). Contactá al profesional.`
})

onMounted(load)

async function load() {
  loading.value = true
  error.value = ''
  try {
    appt.value = await api.get(`/public/appointments/${props.token}`)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function cancel() {
  if (!confirm('¿Seguro que querés cancelar este turno?')) return
  busy.value = true
  error.value = ''
  try {
    appt.value = await api.put(`/public/appointments/${props.token}/cancel`)
    message.value = 'Tu turno fue cancelado. Recibirás un email de confirmación.'
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function startReschedule() {
  rescheduling.value = true
  newSlot.value = null
  slots.value = []
  const base = todayISODate()
  dateOptions.value = Array.from({ length: 14 }, (_, i) => {
    const iso = addDaysISODate(base, i)
    const d = new Date(iso + 'T00:00:00')
    return { iso, label: d.toLocaleDateString('es', { weekday: 'short', day: 'numeric', month: 'short' }) }
  })
}

async function pickDate(iso) {
  selectedDate.value = iso
  newSlot.value = null
  slots.value = await api.get(
    `/public/available-slots?serviceId=${appt.value.service_id}&date=${iso}`
  )
}

async function confirmReschedule() {
  busy.value = true
  error.value = ''
  try {
    appt.value = await api.put(`/public/appointments/${props.token}/reschedule`, {
      new_start_time: newSlot.value.start_time,
    })
    message.value = 'Turno reagendado correctamente.'
    rescheduling.value = false
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-xl space-y-4">
    <h1 class="text-2xl font-bold">Mi turno</h1>

    <Alert v-if="loading">Cargando…</Alert>
    <Alert v-else-if="error && !appt">{{ error }}</Alert>

    <div v-if="appt" class="card space-y-3">
      <Alert v-if="message" type="success">{{ message }}</Alert>
      <Alert v-if="error && rescheduling">{{ error }}</Alert>
      <div class="flex items-center justify-between">
        <div class="text-lg font-semibold">{{ appt.service_name }}</div>
        <StatusBadge :status="appt.status" />
      </div>
      <dl class="grid grid-cols-2 gap-y-1 text-sm">
        <dt class="text-slate-500">Inicio</dt>
        <dd class="font-medium">{{ formatDateTime(appt.start_time) }}</dd>
        <dt class="text-slate-500">Fin</dt>
        <dd class="font-medium">{{ formatDateTime(appt.end_time) }}</dd>
        <dt class="text-slate-500">Cliente</dt>
        <dd class="font-medium">{{ appt.client_name }}</dd>
        <dt class="text-slate-500">Email</dt>
        <dd class="font-medium">{{ appt.client_email }}</dd>
      </dl>

      <div v-if="canManage && !rescheduling" class="flex gap-2 pt-2">
        <button class="btn-secondary" :disabled="busy" @click="startReschedule">Reagendar</button>
        <button class="btn-danger" :disabled="busy" @click="cancel">Cancelar turno</button>
      </div>
      <Alert v-else-if="blockedReason" type="warning">{{ blockedReason }}</Alert>

      <!-- Editor de reagendamiento -->
      <div v-if="rescheduling" class="space-y-3 border-t border-slate-200 pt-4 dark:border-slate-800">
        <p class="text-sm font-medium">Elegí un nuevo horario:</p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="d in dateOptions"
            :key="d.iso"
            class="rounded-full border px-3 py-1 text-xs capitalize"
            :class="selectedDate === d.iso ? 'border-brand-500 bg-brand-500 text-white' : 'border-slate-200 dark:border-slate-700'"
            @click="pickDate(d.iso)"
          >
            {{ d.label }}
          </button>
        </div>
        <div v-if="selectedDate && !slots.length" class="text-sm text-slate-500">Sin horarios ese día.</div>
        <div v-if="slots.length" class="grid grid-cols-4 gap-2">
          <button
            v-for="s in slots"
            :key="s.start_time"
            class="rounded-lg border px-2 py-1.5 text-sm"
            :class="newSlot?.start_time === s.start_time ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-700/20' : 'border-slate-200 dark:border-slate-700'"
            @click="newSlot = s"
          >
            {{ formatTime(s.start_time) }}
          </button>
        </div>
        <div class="flex gap-2">
          <button class="btn-primary" :disabled="!newSlot || busy" @click="confirmReschedule">Confirmar cambio</button>
          <button class="btn-secondary" @click="rescheduling = false">Volver</button>
        </div>
      </div>
    </div>
  </div>
</template>
