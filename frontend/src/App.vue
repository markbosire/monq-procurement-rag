<script lang="ts">
/**
 * Root application component.
 *
 * Renders the current route via `router-view` and displays a global
 * toast notification container at the bottom-right of the viewport.
 *
 * @displayName App
 * @version 1.0.0
 * @example
 * ```vue
 * <App />
 * ```
 */
export {}
</script>

<script setup lang="ts">
// ── State ──
import { X } from 'lucide-vue-next'
import { useToast } from './composables/useToast'

const { toasts, dismiss } = useToast()
</script>

<template>
  <!-- Route content -->
  <router-view />

  <!-- Global toast container -->
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="flex items-start gap-3 px-4 py-3 border-[3px] border-black shadow-neo-lg text-sm font-bold"
        :class="toast.type === 'error' ? 'bg-red-50 text-red-800' : toast.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-blue-50 text-blue-800'"
      >
        <span class="flex-1">{{ toast.message }}</span>
        <button class="shrink-0 mt-0.5" @click="dismiss(toast.id)">
          <X :size="14" />
        </button>
      </div>
    </div>
  </Teleport>
</template>
