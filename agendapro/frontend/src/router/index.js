import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import PublicBooking from '../views/PublicBooking.vue'
import ManageAppointment from '../views/ManageAppointment.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import ProfessionalLayout from '../views/ProfessionalLayout.vue'
import Dashboard from '../views/Dashboard.vue'
import Services from '../views/Services.vue'
import Availability from '../views/Availability.vue'
import Profile from '../views/Profile.vue'

const routes = [
  { path: '/', redirect: '/reservar' },
  { path: '/reservar', name: 'booking', component: PublicBooking },
  { path: '/manage/:token', name: 'manage', component: ManageAppointment, props: true },
  { path: '/login', name: 'login', component: Login },
  { path: '/register', name: 'register', component: Register },
  {
    path: '/app',
    component: ProfessionalLayout,
    meta: { auth: true },
    children: [
      { path: '', redirect: { name: 'dashboard' } },
      { path: 'dashboard', name: 'dashboard', component: Dashboard },
      { path: 'services', name: 'services', component: Services },
      { path: 'availability', name: 'availability', component: Availability },
      { path: 'profile', name: 'profile', component: Profile },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/reservar' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }
  return true
})

export default router
