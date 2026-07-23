<script lang="ts">
/**
 * Document sidebar list.
 *
 * Fetches all documents on mount and renders them as a navigable list.
 * The active document is highlighted. Emits a `select` event when the
 * user clicks a document.
 *
 * @displayName DocumentList
 * @version 1.0.0
 * @example
 * ```vue
 * <DocumentList
 *   :active-id="currentId"
 *   @select="handleSelect"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useDocumentStore } from '../stores/useDocumentStore'

// ── Props ──

defineProps<{
  /** UUID of the currently selected document (or null). */
  activeId: string | null
}>()

// ── Emits ──

const emit = defineEmits<{
  /** User selected a document by its UUID. */
  (e: 'select', id: string): void
}>()

// ── State ──

const store = useDocumentStore()

// ── Lifecycle ──

onMounted(() => store.fetchAll())
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- ── Heading ─────────────────────────────────────────────── -->
    <h2 class="text-lg font-black uppercase mb-3">Documents</h2>

    <!-- ── Loading state ───────────────────────────────────────── -->
    <div v-if="store.loading" class="text-gray-400 text-sm py-4 text-center font-bold">
      Loading...
    </div>

    <!-- ── Empty state ─────────────────────────────────────────── -->
    <div v-else-if="store.documents.length === 0" class="text-gray-400 text-sm py-4 text-center font-bold">
      No documents uploaded yet
    </div>

    <!-- ── Document list ───────────────────────────────────────── -->
    <ul v-else class="flex-1 overflow-y-auto space-y-2">
      <li
        v-for="doc in store.documents"
        :key="doc.document_id"
        :class="[
          'px-3 py-2.5 cursor-pointer text-sm border-2 border-black transition-all',
          doc.document_id === activeId
            ? 'bg-black text-white shadow-neo-sm'
            : 'bg-white hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-neo-sm',
        ]"
        @click="emit('select', doc.document_id)"
      >
        <p class="font-bold truncate">{{ doc.filename }}</p>
        <p :class="doc.document_id === activeId ? 'text-white/70' : 'text-gray-500'" class="text-xs font-mono">
          #{{ doc.document_id }}
          <span v-if="doc.category"> &middot; {{ doc.category }}</span>
          <span> &middot; {{ doc.chunk_count }} chunks</span>
        </p>
      </li>
    </ul>
  </div>
</template>
