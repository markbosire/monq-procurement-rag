/**
 * Application entry point.
 *
 * Initialises the Vue 3 app with the Pinia state management plugin and
 * the Vue Router, then mounts it to the DOM.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.use(createPinia())
app.mount('#app')
