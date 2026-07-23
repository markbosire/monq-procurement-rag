<script lang="ts">
/**
 * PDF navigation toolbar.
 *
 * Displays a "Document Info" toggle button, current page indicator, and
 * prev/next page navigation arrows. Visibility of the page controls is
 * conditionally shown when the metadata panel is not active.
 *
 * @displayName PdfToolbar
 * @version 1.0.0
 * @example
 * ```vue
 * <PdfToolbar
 *   :current-page="1"
 *   :total-pages="10"
 *   :viewing-metadata="false"
 *   :has-metadata="true"
 *   doc-title="My Document"
 *   @go-to-page="goToPage"
 *   @toggle-metadata="toggleMetadata"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

// ── Props ──

/**
 * Current PDF page number (1-indexed).
 */
defineProps<{
  currentPage: number
  /** Total number of pages in the document. */
  totalPages: number
  /** Whether the metadata panel is currently shown instead of the PDF. */
  viewingMetadata: boolean
  /** Whether the document has any metadata to display. */
  hasMetadata: boolean
  /** Document title, used to decide whether to show the info button. */
  docTitle: string | null
}>()

// ── Emits ──

const emit = defineEmits<{
  /** Navigate to a specific page number. */
  (e: 'go-to-page', page: number): void
  /** Toggle between metadata panel and PDF view. */
  (e: 'toggle-metadata'): void
}>()
</script>

<template>
  <!-- ── Toolbar ─────────────────────────────────────────────────── -->
  <div class="flex items-center justify-between px-4 py-2 bg-white border-b-[3px] border-black shrink-0">
    <!-- Left side: info toggle + page indicator -->
    <div class="flex items-center gap-2">
      <button
        v-if="hasMetadata || docTitle"
        class="text-xs px-3 py-1.5 font-bold uppercase border-2 border-black transition-all"
        :class="viewingMetadata ? 'bg-black text-white shadow-neo-sm' : 'bg-white text-gray-700 btn-neo hover:btn-neo-pressed'"
        @click="emit('toggle-metadata')"
      >
        Document Info
      </button>
      <span v-if="!viewingMetadata" class="text-sm font-bold text-gray-600">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
    </div>

    <!-- Right side: navigation arrows -->
    <div v-if="!viewingMetadata" class="flex items-center gap-2">
      <button
        class="neo-icon-btn"
        :disabled="currentPage <= 1"
        aria-label="Previous page"
        @click="emit('go-to-page', currentPage - 1)"
      >
        <ChevronLeft :size="13" />
      </button>
      <button
        class="neo-icon-btn"
        :disabled="currentPage >= totalPages"
        aria-label="Next page"
        @click="emit('go-to-page', currentPage + 1)"
      >
        <ChevronRight :size="13" />
      </button>
    </div>
  </div>
</template>
