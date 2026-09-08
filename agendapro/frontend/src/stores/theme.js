import { ref, watchEffect } from 'vue'

const theme = ref(localStorage.getItem('theme') || 'light')

export function useTheme() {
  watchEffect(() => {
    const root = document.documentElement
    if (theme.value === 'dark') root.classList.add('dark')
    else root.classList.remove('dark')
    localStorage.setItem('theme', theme.value)
  })

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  return { theme, toggle }
}
