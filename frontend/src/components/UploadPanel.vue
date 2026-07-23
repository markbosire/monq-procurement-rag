<script lang="ts">
/**
 * File upload panel.
 *
 * Provides a button-triggered file picker and a drag-and-drop zone for
 * uploading PDF documents. Emits `document-ready` with the new document
 * UUID and a separate `uploaded` event when the upload completes.
 *
 * @displayName UploadPanel
 * @version 1.0.0
 * @example
 * ```vue
 * <UploadPanel
 *   @document-ready="(id) => navigateTo(id)"
 *   @uploaded="refreshList"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref } from 'vue'
import { useDocumentStore } from '../stores/useDocumentStore'
import { useToast } from '../composables/useToast'

// ── Emits ──

const emit = defineEmits<{
  /** A new document was created; provides its UUID. */
  (e: 'document-ready', id: string): void
  /** Upload completed (success or failure). */
  (e: 'uploaded'): void
}>()

// ── State ──

const store = useDocumentStore()
const { show: showToast } = useToast()
const fileInput = ref<HTMLInputElement | null>(null)

// ── Methods ──

/** Handle a file selected via the hidden input element. */
async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('Please select a PDF file')
    return
  }
  const result = await store.upload(file)
  if (result) {
    emit('document-ready', result.document_id)
    emit('uploaded')
  } else if (store.error) {
    showToast(store.error)
  }
}

/** Handle a file dropped onto the drop zone. */
async function handleDrop(event: DragEvent) {
  event.preventDefault()
  const file = event.dataTransfer?.files[0]
  if (!file || !file.name.toLowerCase().endsWith('.pdf')) return
  const result = await store.upload(file)
  if (result) {
    emit('document-ready', result.document_id)
    emit('uploaded')
  } else if (store.error) {
    showToast(store.error)
  }
}

/** Prevent default drag-over behaviour. */
function handleDragOver(event: DragEvent) {
  event.preventDefault()
}
</script>

<template>
  <div class="flex items-center gap-3">
    <input
      ref="fileInput"
      type="file"
      accept=".pdf"
      class="hidden"
      @change="onFileSelected"
    />
    <button
      :disabled="store.uploading"
      class="px-4 py-2 text-sm font-bold uppercase border-2 border-black btn-neo hover:btn-neo-pressed disabled:opacity-40 disabled:hover:shadow-neo disabled:hover:translate-x-0 disabled:hover:translate-y-0 bg-black text-white"
      @click="fileInput?.click()"
    >
      {{ store.uploading ? 'Uploading...' : 'Upload PDF' }}
    </button>
    <div
      class="border-2 border-dashed border-black px-4 py-2 text-sm font-bold text-gray-500 cursor-pointer hover:bg-gray-100 transition-colors flex-1 rounded-none"
      @drop="handleDrop"
      @dragover="handleDragOver"
      @click="fileInput?.click()"
    >
      or drop a PDF here
    </div>
  </div>
</template>
