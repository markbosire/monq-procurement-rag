/**
 * Global toast notification composable.
 *
 * Maintains a singleton reactive array of toast messages that can be
 * displayed anywhere in the application. Each toast auto-dismisses
 * after 5 seconds.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { reactive, readonly } from 'vue'

// ── Types ──────────────────────────────────────────────────────────

/** A single toast notification. */
export interface Toast {
  /** Unique identifier used for dismissal. */
  id: number
  /** Message text to display. */
  message: string
  /** Visual style variant. */
  type: 'error' | 'success' | 'info'
}

// ── State ──────────────────────────────────────────────────────────

/** Internal mutable state shared across all callers. */
const state = reactive({
  toasts: [] as Toast[],
})

/** Monotonically increasing id counter. */
let nextId = 0

// ── Composable ─────────────────────────────────────────────────────

/**
 * Composable for showing toast notifications globally.
 *
 * @returns Reactive toasts array and action methods.
 */
export function useToast() {
  /**
   * Display a toast notification.
   *
   * The toast is automatically removed after 5 seconds.
   *
   * @param message - Text to display.
   * @param type    - Visual style (default: 'error').
   */
  function show(message: string, type: Toast['type'] = 'error') {
    const id = nextId++
    state.toasts.push({ id, message, type })
    setTimeout(() => {
      const idx = state.toasts.findIndex(t => t.id === id)
      if (idx !== -1) state.toasts.splice(idx, 1)
    }, 5000)
  }

  /**
   * Dismiss a toast by its id.
   *
   * @param id - The toast identifier.
   */
  function dismiss(id: number) {
    const idx = state.toasts.findIndex(t => t.id === id)
    if (idx !== -1) state.toasts.splice(idx, 1)
  }

  /** Clear all visible toasts immediately. */
  function clear() {
    state.toasts.splice(0, state.toasts.length)
  }

  return { toasts: readonly(state).toasts, show, dismiss, clear }
}
