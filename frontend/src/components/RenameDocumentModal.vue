<script lang="ts">
/**
 * Inline rename input for a document.
 *
 * Displays an input field and Save/Cancel buttons inline in the document
 * card. Emits `update:modelValue` on cancel and `confirm` with the new
 * name on save.
 *
 * @displayName RenameDocumentModal
 * @version 1.0.0
 * @example
 * ```vue
 * <RenameDocumentModal
 *   :model-value="isRenaming"
 *   :initial-name="doc.filename"
 *   @update:model-value="isRenaming = false"
 *   @confirm="(name) => handleRename(docId, name)"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref, watch } from 'vue'

// ── Props ──

const props = defineProps<{
  /** Whether the rename input is visible. */
  modelValue: boolean
  /** Initial filename to populate the input. */
  initialName: string
}>()

// ── Emits ──

const emit = defineEmits<{
  /** Close the inline input via v-model update. */
  (e: 'update:modelValue', v: boolean): void
  /** Confirm the new name. */
  (e: 'confirm', name: string): void
}>()

// ── State ──

const name = ref(props.initialName)

// ── Watchers ──

watch(() => props.initialName, (v) => { name.value = v })

// ── Methods ──

/** Emit the new name and close. */
function onConfirm() {
  if (!name.value.trim()) return
  emit('confirm', name.value.trim())
}

/** Emit a close event via v-model update. */
function onCancel() {
  emit('update:modelValue', false)
}
</script>

<template>
  <div v-if="modelValue" class="flex items-center gap-2">
    <input
      v-model="name"
      class="w-full input-neo focus:input-neo-focus px-2 py-1 text-sm"
      autofocus
      @keyup.enter="onConfirm"
      @keyup.escape="onCancel"
    />
    <button
      class="text-xs font-bold uppercase px-3 py-1 bg-black text-white border-2 border-black btn-neo hover:btn-neo-pressed"
      @click="onConfirm"
    >
      Save
    </button>
    <button
      class="text-xs font-bold uppercase px-3 py-1 border-2 border-black btn-neo hover:btn-neo-pressed"
      @click="onCancel"
    >
      Cancel
    </button>
  </div>
</template>
