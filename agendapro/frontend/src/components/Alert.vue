<script setup>
defineProps({
  type: { type: String, default: 'error' },
})
</script>

<template>
  <div
    v-if="$slots.default"
    class="rounded-lg px-3 py-2 text-sm"
    :class="{
      'bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300': type === 'error',
      'bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300': type === 'success',
      'bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-200': type === 'warning',
    }"
  >
    <slot />
  </div>
</template>
