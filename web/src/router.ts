import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import AuthCallback from './views/AuthCallback.vue'
import DeviceTypes from './views/DeviceTypes.vue'
import Devices from './views/Devices.vue'
import Bindings from './views/Bindings.vue'
import ActionsTest from './views/ActionsTest.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/auth/callback', component: AuthCallback },
    { path: '/device-types', component: DeviceTypes },
    { path: '/devices', component: Devices },
    { path: '/bindings', component: Bindings },
    { path: '/test', component: ActionsTest }
  ]
})

