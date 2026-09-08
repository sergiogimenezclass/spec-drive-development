<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import Alert from '../components/Alert.vue'

const services = ref([])
const error = ref('')
const message = ref('')
const editing = ref(null) // null = nuevo, objeto = editando
const form = ref({ name: '', duration_minutes: 30, description: '' })
const loading = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  try {
    services.value = await api.get('/professional/services', { auth: true })
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function startNew() {
  editing.value = {}
  form.value = { name: '', duration_minutes: 30, description: '' }
  error.value = ''
  message.value = ''
}

function startEdit(s) {
  editing.value = s
  form.value = { name: s.name, duration_minutes: s.duration_minutes, description: s.description || '' }
  error.value = ''
}

async function save() {
  error.value = ''
  message.value = ''
  try {
    if (editing.value && editing.value.id) {
      const updated = await api.put(`/professional/services/${editing.value.id}`, form.value, { auth: true })
      Object.assign(editing.value, updated)
      message.value = 'Servicio actualizado.'
    } else {
      const created = await api.post('/professional/services', form.value, { auth: true })
      services.value.push(created)
      message.value = 'Servicio creado.'
    }
    editing.value = null
  } catch (e) {
    error.value = e.message
  }
}

async function remove(s) {
  if (!confirm(`¿Eliminar el servicio "${s.name}"?`)) return
  error.value = ''
  try {
    await api.del(`/professional/services/${s.id}`, { auth: true })
    services.value = services.value.filter((x) => x.id !== s.id)
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Servicios</h1>
      <button class="btn-primary" @click="startNew">Nuevo servicio</button>
    </div>

    <Alert v-if="error">{{ error }}</Alert>
    <Alert v-if="message" type="success">{{ message }}</Alert>

    <div v-if="editing !== null" class="card space-y-3">
      <h2 class="font-semibold">{{ editing.id ? 'Editar servicio' : 'Nuevo servicio' }}</h2>
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="label">Nombre</label>
          <input v-model="form.name" class="input" placeholder="Ej: Corte de pelo" />
        </div>
        <div>
          <label class="label">Duración (minutos)</label>
          <input v-model.number="form.duration_minutes" type="number" min="5" class="input" />
        </div>
        <div class="sm:col-span-2">
          <label class="label">Descripción (opcional)</label>
          <input v-model="form.description" class="input" />
        </div>
      </div>
      <div class="flex gap-2">
        <button class="btn-primary" @click="save">Guardar</button>
        <button class="btn-secondary" @click="editing = null">Descartar</button>
      </div>
    </div>

    <div v-if="loading" class="text-sm text-slate-500">Cargando…</div>
    <div v-else-if="!services.length" class="card text-sm text-slate-500">
      Todavía no creaste servicios. Los clientes solo podrán reservar turnos de servicios que existan.
    </div>

    <div v-else class="space-y-2">
      <div v-for="s in services" :key="s.id" class="card flex items-center justify-between">
        <div>
          <div class="font-medium">{{ s.name }}</div>
          <div class="text-sm text-slate-500">{{ s.duration_minutes }} min · {{ s.description || 'Sin descripción' }}</div>
        </div>
        <div class="flex gap-2">
          <button class="btn-secondary" @click="startEdit(s)">Editar</button>
          <button class="btn-danger" @click="remove(s)">Eliminar</button>
        </div>
      </div>
    </div>
  </div>
</template>
