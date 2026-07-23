<script lang="ts">
/**
 * Chat panel for document Q&A.
 *
 * Provides the message list, input field, and send button for asking
 * questions about a specific document. Integrates with the chat store
 * for state management and the source viewer for PDF highlighting.
 *
 * @displayName ChatPanel
 * @version 1.0.0
 * @example
 * ```vue
 * <ChatPanel
 *   document-id="uuid"
 *   :theme="theme"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ArrowRight } from 'lucide-vue-next'
import { useChatStore } from '../stores/useChatStore'
import { useSourceViewer } from '../composables/useSourceViewer'
import type { TypeTheme } from '../constants/documentTypeTheme'
import type { BBox } from '../api/chat'
import ChatMessage from './ChatMessage.vue'
import DocumentViewerModal from './DocumentViewerModal.vue'

const props = defineProps<{
  /** UUID of the document to chat about. */
  documentId: string
  /** Visual theme for the document category. */
  theme: TypeTheme
}>()

const chatStore = useChatStore()
const { showHighlight } = useSourceViewer()

// ── Local state ────────────────────────────────────────────────────────

/** Current user input text. */
const question = ref('')
/** Reference to the scrollable message container for auto-scroll. */
const chatContainer = ref<HTMLDivElement | null>(null)

/** State for the fallback PDF modal viewer. */
interface ViewerState {
  chunkId: number
  chunkText: string
  bbox?: BBox[]
}

const viewer = ref<ViewerState | null>(null)

// ── Lifecycle ──────────────────────────────────────────────────────────

onMounted(async () => {
  await chatStore.loadHistory(props.documentId)
  await nextTick()
  chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
})

// ── Methods ────────────────────────────────────────────────────────────

/** Send the current question and auto-scroll to the bottom. */
async function sendMessage() {
  const q = question.value.trim()
  if (!q || chatStore.loading) return
  question.value = ''
  await chatStore.send(props.documentId, q)
  await nextTick()
  chatContainer.value?.scrollTo({ top: chatContainer.value.scrollHeight, behavior: 'smooth' })
}

/**
 * Handle a source-click event from a ChatMessage component.
 *
 * If the chunk has bounding boxes, broadcast the highlight via the
 * source viewer so the PDF panel can navigate to it.
 *
 * @param data - Chunk id and bounding boxes.
 */
function handleSourceClick(data: { chunkId: number; bbox: BBox[] }) {
  if (data.bbox && data.bbox.length > 0) {
    showHighlight({ chunkId: data.chunkId, bbox: data.bbox })
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- ── Scrollable message area ───────────────────────────────── -->
    <div
      ref="chatContainer"
      class="flex-1 overflow-y-auto space-y-3 px-4 py-3"
    >
      <p v-if="chatStore.messages.length === 0" class="text-gray-500 text-center mt-8 text-sm font-bold">
        Ask a question about this document
      </p>
      <ChatMessage
        v-for="(msg, i) in chatStore.messages"
        :key="i"
        :role="msg.role"
        :content="msg.content"
        :document-id="documentId"
        :source-chunks="msg.source_chunks"
        :theme="theme"
        @source-click="handleSourceClick"
      />
      <div v-if="chatStore.loading" class="flex items-center gap-2 px-1 py-1">
        <div class="font-mono font-bold text-[10px] tracking-wider border-2 border-black bg-white px-2 py-1.5 flex items-center gap-1.5">
          THINKING
          <span class="neo-dot" />
          <span class="neo-dot" />
          <span class="neo-dot" />
        </div>
      </div>
      <p v-if="chatStore.error" class="text-red-600 text-sm font-bold">{{ chatStore.error }}</p>
    </div>

    <!-- ── Input area ────────────────────────────────────────────── -->
    <div class="shrink-0 px-4 py-3 flex gap-2 border-t-[3px] border-black">
      <input
        v-model="question"
        type="text"
        placeholder="Type your question..."
        class="flex-1 px-3 py-2 text-sm input-neo focus:input-neo-focus bg-white text-gray-800 placeholder-gray-400"
        @keyup.enter="sendMessage"
      />
      <button
        :disabled="chatStore.loading || !question.trim()"
        class="px-3.5 text-sm font-bold tracking-wide uppercase border-2 border-black btn-neo hover:btn-neo-pressed disabled:opacity-40 disabled:hover:shadow-neo disabled:hover:translate-x-0 disabled:hover:translate-y-0 active:translate-x-[3px] active:translate-y-[3px] active:shadow-[1px_1px_0_0_rgba(0,0,0,1)] flex items-center gap-1.5"
        :style="{ backgroundColor: chatStore.loading || !question.trim() ? '#9ca3af' : theme.color, color: '#fff' }"
        @click="sendMessage"
      >
        Send
        <ArrowRight :size="13" />
      </button>
    </div>

    <!-- ── Fallback PDF viewer modal ─────────────────────────────── -->
    <DocumentViewerModal
      v-if="viewer"
      :document-id="documentId"
      :chunk-id="viewer.chunkId"
      :chunk-text="viewer.chunkText"
      :bbox="viewer.bbox"
      @close="viewer = null"
    />
  </div>
</template>
