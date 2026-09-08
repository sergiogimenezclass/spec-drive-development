<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api/client'
import Alert from '../components/Alert.vue'
import { formatTime, todayISODate, addDaysISODate } from '../utils/format'

const services = ref([])
const selectedService = ref(null)
const dateOptions = ref([])
const selectedDate = ref(null)
const slots = ref([])
const selectedSlot = ref(null)
const loadingSlots = ref(false)

const client = ref({ client_name: '', client_email: '', client_phone: '', notes: '' })
const submitting = ref(false)
const error = ref('')
const created = ref(null)

const step = computed(() => {
  if (created.value) return 'done'
  if (selectedSlot.value) return 'data'
  if (selectedService.value) return 'slots'
  return 'service'
})

onMounted(async () => {
  services.value = await api.get('/public/services')
  if (services.value.length === 1) selectService(services.value[0])
  const base = todayISODate()
  dateOptions.value = Array.from({ length: 14 }, (_, i) => {
    const iso = addDaysISODate(base, i)
    const d = new Date(iso + 'T00:00:00')
    return { iso, label: d.toLocaleDateString('es', { weekday: 'short', day: 'numeric', month: 'short' }) }
  })
})

async function selectService(svc) {
  selectedService.value = svc
  selectedSlot.value = null
  slots.value = []
  if (selectedDate.value) await loadSlots()
}

async function selectDate(iso) {
  selectedDate.value = iso
  selectedSlot.value = null
  await loadSlots()
}

async function loadSlots() {
  if (!selectedService.value || !selectedDate.value) return
  loadingSlots.value = true
  error.value = ''
  try {
    slots.value = await api.get(
      `/public/available-slots?serviceId=${selectedService.value.id}&date=${selectedDate.value}`
    )
  } catch (e) {
    error.value = e.message
  } finally {
    loadingSlots.value = false
  }
}

async function confirm() {
  submitting.value = true
  error.value = ''
  try {
    created.value = await api.post('/public/appointments', {
      service_id: selectedService.value.id,
      start_time: selectedSlot.value.start_time,
      ...client.value,
    })
  } catch (e) {
    error.value = e.message
    if (e.code === 'ALREADY_BOOKED') {
      await loadSlots()
      selectedSlot.value = null
    }
  } finally {
    submitting.value = false
  }
}

function reset() {
  created.value = null
  selectedSlot.value = null
  client.value = { client_name: '', client_email: '', client_phone: '', notes: '' }
  loadSlots()
}

const manageUrl = computed(() =>
  created.value ? `${window.location.origin}/manage/${created.value.booking_token}` : ''
)
</script>

<template>
  <div class="mx-auto max-w-2xl space-y-6">
    <div>
      <h1 class="text-2xl font-bold">Reservá tu turno</h1>
      <p class="text-sm text-slate-500">Elegí el servicio, el día y el horario que mejor te quede.</p>
    </div>

    <!-- Paso: servicio -->
    <div class="card">
      <h2 class="mb-3 font-semibold">1. Servicio</h2>
      <div v-if="!services.length" class="text-sm text-slate-500">No hay servicios disponibles para reservar todavía.</div>
      <div v-else class="grid gap-3 sm:grid-cols-2">
        <button
          v-for="s in services"
          :key="s.id"
          class="rounded-lg border p-4 text-left transition"
          :class="selectedService?.id === s.id ? 'border-brand-500 ring-2 ring-brand-500/30' : 'border-slate-200 hover:border-brand-300 dark:border-slate-700'"
          @click="selectService(s)"
        >
          <div class="font-medium">{{ s.name }}</div>
          <div class="text-xs text-slate-500">{{ s.duration_minutes }} min</div>
          <div v-if="s.description" class="mt-1 text-sm text-slate-500">{{ s.description }}</div>
        </button>
      </div>
    </div>

    <!-- Paso: fecha + slots -->
    <div v-if="selectedService" class="card">
      <h2 class="mb-3 font-semibold">2. Fecha y horario</h2>
      <div class="mb-4 flex flex-wrap gap-2">
        <button
          v-for="d in dateOptions"
          :key="d.iso"
          class="rounded-full border px-3 py-1 text-xs capitalize transition"
          :class="selectedDate === d.iso ? 'border-brand-500 bg-brand-500 text-white' : 'border-slate-200 hover:border-brand-300 dark:border-slate-700'"
          @click="selectDate(d.iso)"
        >
          {{ d.label }}
        </button>
      </div>
      <Alert v-if="error && step !== 'data'">{{ error }}</Alert>
      <div v-if="!selectedDate" class="text-sm text-slate-500">Elegí una fecha para ver los horarios.</div>
      <div v-else-if="loadingSlots" class="text-sm text-slate-500">Cargando disponibilidad…</div>
      <div v-else-if="!slots.length" class="text-sm text-slate-500">No hay horarios disponibles ese día. Probá otra fecha.</div>
      <div v-else class="grid grid-cols-3 gap-2 sm:grid-cols-4">
        <button
          v-for="s in slots"
          :key="s.start_time"
          class="rounded-lg border px-2 py-2 text-sm transition"
          :class="selectedSlot?.start_time === s.start_time ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-700/20 dark:text-brand-100' : 'border-slate-200 hover:border-brand-300 dark:border-slate-700'"
          @click="selectedSlot = s"
        >
          {{ formatTime(s.start_time) }}
        </button>
      </div>
    </div>

    <!-- Paso: datos + confirmar -->
    <div v-if="selectedSlot" class="card">
      <h2 class="mb-3 font-semibold">3. Tus datos</h2>
      <Alert v-if="error">{{ error }}</Alert>
      <div class="mb-4 rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800">
        <strong>{{ selectedService.name }}</strong> · {{ formatTime(selectedSlot.start_time) }}
      </div>
      <form class="grid gap-4 sm:grid-cols-2" @submit.prevent="confirm">
        <div>
          <label class="label">Nombre y apellido</label>
          <input v-model="client.client_name" class="input" required />
        </div>
        <div>
          <label class="label">Email</label>
          <input v-model="client.client_email" type="email" class="input" required />
        </div>
        <div>
          <label class="label">Teléfono (opcional)</label>
          <input v-model="client.client_phone" class="input" />
        </div>
        <div class="sm:col-span-2">
          <label class="label">Notas (opcional)</label>
          <textarea v-model="client.notes" class="input" rows="2"></textarea>
        </div>
        <div class="sm:col-span-2">
          <button class="btn-primary w-full" :disabled="submitting">
            {{ submitting ? 'Reservando…' : 'Confirmar reserva' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Confirmación -->
    <div v-if="created" class="card border-green-200 dark:border-green-900">
      <h2 class="mb-2 text-lg font-semibold text-green-700 dark:text-green-400">¡Reserva confirmada!</h2>
      <p class="text-sm text-slate-600 dark:text-slate-300">
        Te enviamos un email de confirmación. Podés autogestionar tu turno con este enlace personal:
      </p>
      <div class="mt-3 flex items-center gap-2">
        <input class="input" readonly :value="manageUrl" @focus="$event.target.select()" />
        <a class="btn-secondary" :href="`#/manage/${created.booking_token}`" @click.prevent="$router.push(`/manage/${created.booking_token}`)">Ir</a>
      </div>
      <button class="btn-secondary mt-4" @click="reset">Reservar otro turno</button>
    </div>
  </div>
</template>
