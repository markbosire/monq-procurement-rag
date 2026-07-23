<script lang="ts">
/**
 * Chat message bubble.
 *
 * Renders a single chat message with a role badge ("YOU" / "AI"), the
 * message content, a copy-to-clipboard button, and an expandable source
 * chunks grid. Clicking a source chunk emits a source-click event for
 * PDF highlighting.
 *
 * @displayName ChatMessage
 * @version 1.0.0
 * @example
 * ```vue
 * <ChatMessage
 *   role="assistant"
 *   content="Here is the answer..."
 *   document-id="uuid"
 *   :source-chunks="chunks"
 *   :theme="theme"
 *   @source-click="handleSourceClick"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref } from 'vue'
import { Copy, ChevronDown } from 'lucide-vue-next'
import type { SourceChunk, BBox } from '../api/chat'
import type { TypeTheme } from '../constants/documentTypeTheme'
import DocumentViewerModal from './DocumentViewerModal.vue'

const props = defineProps<{
  /** Message sender role. */
  role: 'user' | 'assistant'
  /** Message body text. */
  content: string
  /** Document UUID for the PDF viewer modal. */
  documentId: string
  /** Source chunks cited by the assistant (empty for user). */
  sourceChunks?: SourceChunk[]
  /** Visual theme for the document category. */
  theme: TypeTheme
}>()

const emit = defineEmits<{
  /**
   * User clicked a source chunk that has bounding boxes.
   * The parent should navigate the PDF viewer to this chunk.
   */
  (e: 'source-click', data: { chunkId: number; bbox: BBox[] }): void
}>()

// ── Local state ────────────────────────────────────────────────────────

/** Whether the copy-to-clipboard confirmation is visible. */
const copied = ref(false)
/** Whether the source chunks accordion is expanded. */
const sourcesOpen = ref(false)

/** State for the PDF modal viewer (used when a chunk has no bbox). */
interface ViewerState {
  chunkId: number
  chunkText: string
  bbox?: BBox[]
}

const viewer = ref<ViewerState | null>(null)

// ── Methods ────────────────────────────────────────────────────────────

/**
 * Open the source viewer for a chunk.
 *
 * If the chunk has bounding boxes, emit a source-click event so the
 * parent can highlight the PDF. Otherwise open a modal viewer.
 *
 * @param chunk - The source chunk to view.
 */
function openViewer(chunk: SourceChunk) {
  if (chunk.bbox && chunk.bbox.length > 0) {
    emit('source-click', { chunkId: chunk.id, bbox: chunk.bbox })
  } else {
    viewer.value = { chunkId: chunk.id, chunkText: chunk.text, bbox: chunk.bbox }
  }
}

/** Close the PDF modal viewer. */
function closeViewer() {
  viewer.value = null
}

/** Copy the message content to the system clipboard. */
async function copyContent() {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Clipboard API not available.
  }
}
</script>

<template>
  <div>
    <!-- ── User bubble ───────────────────────────────────────────── -->
    <div v-if="role === 'user'" class="flex justify-end relative mt-5">
      <span
        class="absolute -top-3 right-3 z-10 font-mono font-bold text-[10px] tracking-widest text-white border-2 border-black px-2 py-0.5"
        :style="{ backgroundColor: '#0a0a0a' }"
      >YOU</span>
      <div
        class="border-[3px] border-black px-4 py-3 leading-relaxed text-white max-w-[80%]"
        :style="{ backgroundColor: theme.color, boxShadow: `5px 5px 0 ${theme.color}` }"
      >
        {{ content }}
      </div>
    </div>

    <!-- ── Assistant bubble ──────────────────────────────────────── -->
    <div v-else class="relative mt-5">
      <span
        class="absolute -top-3 left-3 z-10 font-mono font-bold text-[10px] tracking-widest text-white border-2 border-black px-2 py-0.5"
        :style="{ backgroundColor: theme.color }"
      >AI</span>
      <div
        class="bg-white border-[3px] border-black px-4 py-4"
        :style="{ boxShadow: `5px 5px 0 ${theme.color}` }"
      >
        <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ content }}</p>

        <!-- ── Footer: sources toggle + copy ─────────────────────── -->
        <div class="mt-3 pt-3 flex items-center justify-between" style="border-top: 2px dashed #cfcabf">
          <button
            v-if="sourceChunks && sourceChunks.length > 0"
            class="neo-src-toggle"
            @click="sourcesOpen = !sourcesOpen"
          >
            SOURCES ({{ sourceChunks.length }})
            <ChevronDown
              :size="13"
              :class="sourcesOpen ? 'rotate-180' : ''"
              class="transition-transform duration-150"
            />
          </button>
          <div v-else />
          <button
            class="neo-icon-btn"
            :style="{ backgroundColor: copied ? '#000' : '#fff', color: copied ? '#fff' : '#000' }"
            @click="copyContent"
            aria-label="Copy response text"
          >
            <Copy :size="13" />
          </button>
        </div>

        <!-- ── Source chips grid ─────────────────────────────────── -->
        <div
          v-if="sourceChunks && sourceChunks.length > 0 && sourcesOpen"
          class="mt-3 grid grid-cols-2 gap-2"
        >
          <div
            v-for="(chunk, i) in sourceChunks"
            :key="i"
            class="neo-chip"
            :style="{ borderLeftColor: theme.color, backgroundColor: theme.color + '12' }"
            @click="openViewer(chunk)"
          >
            <div class="font-display text-[10px]">CHUNK {{ i + 1 }}</div>
            <div
              v-if="chunk.page_numbers && chunk.page_numbers.length > 0"
              class="font-mono text-[9px] mt-0.5"
              :style="{ color: theme.color }"
            >
              [p. {{ chunk.page_numbers.join(', ') }}]
            </div>
            <div class="text-[10px] text-[#444] leading-tight mt-0.5 line-clamp-2">{{ chunk.text }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── PDF viewer modal (no-bbox fallback) ───────────────────── -->
    <DocumentViewerModal
      v-if="viewer"
      :document-id="documentId"
      :chunk-id="viewer.chunkId"
      :chunk-text="viewer.chunkText"
      :bbox="viewer.bbox"
      @close="closeViewer"
    />
  </div>
</template>
