<script lang="ts">
/**
 * Document chat page.
 *
 * Displays a side-by-side layout with a PDF viewer and a chat panel
 * for asking questions about a specific document. On small screens the
 * PDF viewer is shown in a modal overlay triggered by a header button.
 *
 * @displayName DocumentChatPage
 * @version 1.0.0
 * @example
 * ```vue
 * <DocumentChatPage id="uuid" />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, FileText } from 'lucide-vue-next'
import { getTypeTheme } from '../constants/documentTypeTheme'
import type { TypeTheme } from '../constants/documentTypeTheme'
import { activeHighlight } from '../composables/useSourceViewer'
import { useChatStore } from '../stores/useChatStore'
import DocumentViewer from '../components/DocumentViewerPanel.vue'
import ChatPanel from '../components/ChatPanel.vue'

// ── Props ──

const props = defineProps<{
  /** Document UUID to display and chat about. */
  id: string
}>()

// ── State ──

const router = useRouter()
const chatStore = useChatStore()
const windowWidth = ref(window.innerWidth)
const showPdfModal = ref(false)

// ── Computed ──

const isBelowLg = computed(() => windowWidth.value < 1024)
const isBelowXl = computed(() => windowWidth.value < 1200)

const pdfFlex = computed(() => isBelowXl.value ? 'flex-[5]' : 'flex-[3]')
const chatFlex = computed(() => isBelowXl.value ? 'flex-[2]' : 'flex-[4]')

const theme = computed<TypeTheme>(() => getTypeTheme(chatStore.documentInfo?.classification?.category))

// ── Methods ──

/** Update windowWidth ref on browser resize. */
function onResize() {
  windowWidth.value = window.innerWidth
}

// ── Watchers ──

watch(activeHighlight, (hl) => {
  if (hl && isBelowLg.value) {
    showPdfModal.value = true
  }
})

// ── Lifecycle ──

onMounted(async () => {
  const found = await chatStore.loadDocumentInfo(props.id)
  if (!found) {
    router.replace('/not-found')
    return
  }
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <!-- ── Header ─────────────────────────────────────────────────── -->
    <header
      class="flex items-center gap-3 px-4 py-3 shrink-0 border-b-[3px] border-black"
      :style="{ backgroundColor: theme.color }"
    >
      <button
        class="p-1.5 border-[3px] border-black btn-neo hover:btn-neo-pressed text-white bg-transparent"
        @click="router.push('/documents')"
      >
        <ArrowLeft :size="18" />
      </button>
      <component
        v-if="!chatStore.documentInfo"
        :is="theme.icon"
        :size="18"
        :stroke-width="2"
        class="text-white"
      />
      <div v-if="chatStore.documentInfo" class="flex-1 min-w-0">
        <h1 class="text-sm font-bold truncate text-white">{{ chatStore.documentInfo.title }}</h1>
      </div>
      <div v-else class="text-sm text-white/70 flex-1 font-bold">Loading...</div>

      <button
        v-if="chatStore.documentInfo && isBelowLg"
        class="text-xs px-3 py-1.5 font-bold uppercase border-[3px] border-black btn-neo hover:btn-neo-pressed bg-white text-gray-900 flex items-center gap-1.5"
        @click="showPdfModal = true"
      >
        <FileText :size="14" />
        PDF
      </button>
    </header>

    <!-- ── Desktop layout: PDF + Chat side-by-side ────────────────── -->
    <main v-if="chatStore.documentInfo && !isBelowLg" class="flex-1 flex overflow-hidden">
      <div :class="[pdfFlex, 'flex flex-col overflow-hidden']">
        <DocumentViewer :document-id="id" />
      </div>
      <div class="w-[3px] bg-black shrink-0" />
      <div :class="[chatFlex, 'flex flex-col overflow-hidden']">
        <ChatPanel :document-id="id" :theme="theme" />
      </div>
    </main>

    <!-- ── Mobile layout: Chat only ───────────────────────────────── -->
    <main v-else-if="chatStore.documentInfo && isBelowLg" class="flex-1 flex overflow-hidden">
      <div class="flex-1 flex flex-col overflow-hidden">
        <ChatPanel :document-id="id" :theme="theme" />
      </div>
    </main>

    <!-- ── PDF modal overlay (mobile) ─────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showPdfModal && isBelowLg"
        class="fixed inset-0 z-50 bg-[#f7f4ec] flex flex-col"
      >
        <div class="flex items-center justify-between px-4 py-3 border-b-[3px] border-black shrink-0 bg-white">
          <span class="font-bold text-sm uppercase tracking-wider">Document PDF</span>
          <button
            class="text-sm px-3 py-1.5 font-bold uppercase border-2 border-black btn-neo hover:btn-neo-pressed"
            @click="showPdfModal = false"
          >
            Close
          </button>
        </div>
        <div class="flex-1 overflow-hidden flex flex-col">
          <DocumentViewer :document-id="id" />
        </div>
      </div>
    </Teleport>
  </div>
</template>
