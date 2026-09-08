<script setup>
import { computed } from 'vue'
const props = defineProps({ status: String })
const map = {
  BOOKED: ['Reservado', 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300'],
  CANCELLED: ['Cancelado', 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300'],
  COMPLETED: ['Completado', 'bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-300'],
  NO_SHOW: ['No presentado', 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200'],
}
const info = computed(() => map[props.status] || [props.status || '—', 'bg-slate-100 text-slate-600'])
</script>

<template>
  <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium" :class="info[1]">
    {{ info[0] }}
  </span>
</template>
