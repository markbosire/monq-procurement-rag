<script lang="ts">
/**
 * Delete confirmation modal.
 *
 * Displays a modal dialog asking the user to confirm document deletion.
 * Emits `update:modelValue` on cancel and `confirm` on confirmation.
 *
 * @displayName DeleteConfirmModal
 * @version 1.0.0
 * @example
 * ```vue
 * <DeleteConfirmModal
 *   :model-value="isOpen"
 *   @update:model-value="isOpen = false"
 *   @confirm="handleDelete"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
// ── Props ──

defineProps<{
  /** Whether the modal is visible. */
  modelValue: boolean
}>()

// ── Emits ──

const emit = defineEmits<{
  /** Close the modal by updating v-model. */
  (e: 'update:modelValue', v: boolean): void
  /** User confirmed the delete action. */
  (e: 'confirm'): void
}>()

// ── Methods ──

/** Emit a close event via v-model update. */
function onCancel() {
  emit('update:modelValue', false)
}
</script>

<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click="onCancel"
  >
    <!-- ── Dialog ──────────────────────────────────────────────── -->
    <div class="bg-white rounded-none border-2 border-black p-6 max-w-sm w-full mx-4 shadow-neo-lg" @click.stop>
      <h3 class="font-display text-lg uppercase mb-3">Delete document?</h3>
      <p class="text-sm text-gray-600 mb-5 font-medium">
        This will permanently delete the document, its chunks, and chat history. This cannot be undone.
      </p>
      <div class="flex justify-end gap-3">
        <button
          class="px-4 py-2 text-sm font-bold uppercase border-2 border-black btn-neo hover:btn-neo-pressed"
          @click="onCancel"
        >
          Cancel
        </button>
        <button
          class="px-4 py-2 text-sm font-bold uppercase text-white bg-red-600 border-2 border-black btn-neo hover:btn-neo-pressed"
          @click="emit('confirm')"
        >
          Delete
        </button>
      </div>
    </div>
  </div>
</template>
