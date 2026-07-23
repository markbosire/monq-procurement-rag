<script lang="ts">
/**
 * PDF viewer modal for viewing source chunks without bounding boxes.
 *
 * Renders a single PDF page with optional highlight overlays inside a
 * full-screen modal. The user can navigate pages via prev/next buttons
 * or a direct page input. The modal is positioned on top of the current
 * viewport with a semi-transparent backdrop.
 *
 * @displayName DocumentViewerModal
 * @version 1.0.0
 * @example
 * ```vue
 * <DocumentViewerModal
 *   document-id="uuid"
 *   :chunk-id="42"
 *   chunk-text="Some chunk text"
 *   :bbox="bboxes"
 *   @close="closeViewer"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import * as pdfjsLib from 'pdfjs-dist'
import { getTypeTheme } from '../constants/documentTypeTheme'
import type { TypeTheme } from '../constants/documentTypeTheme'
import { getDocument, getDocumentPdf } from '../api/documents'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

// ── Types ──

/** Bounding-box rectangle for a PDF highlight. */
interface BBox {
  page: number
  x0: number
  y0: number
  x1: number
  y1: number
}

// ── Constants ──

/** Padding around the canvas inside its container (px). */
const PADDING = 32

// ── Props ──

const props = defineProps<{
  /** UUID of the document to display. */
  documentId: string
  /** ID of the source chunk to highlight. */
  chunkId: number
  /** Text of the source chunk. */
  chunkText: string
  /** Optional bounding boxes for highlight overlays. */
  bbox?: BBox[]
}>()

// ── Emits ──

const emit = defineEmits<{
  /** User closed the modal. */
  (e: 'close'): void
}>()

// ── State ──

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const currentPage = ref(1)
const totalPages = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)
let theme: TypeTheme = getTypeTheme(null)

/** Loaded pdfjs document proxy. */
let pdfDoc: pdfjsLib.PDFDocumentProxy | null = null
/** Bounding boxes to highlight on the rendered page. */
let highlightBBoxes: BBox[] = []

// ── Methods ──

/**
 * Compute the scale factor so the page fits within the container.
 *
 * @param pageHeight - Full page height at 1x scale.
 * @param pageWidth  - Full page width at 1x scale.
 * @returns The scale factor to apply.
 */
function computeFitScale(pageHeight: number, pageWidth: number): number {
  if (!containerRef.value) return 1
  const ch = containerRef.value.clientHeight - PADDING
  const cw = containerRef.value.clientWidth - PADDING
  if (ch <= 0 || cw <= 0) return 1
  const scaleH = ch / pageHeight
  const scaleW = cw / pageWidth
  return Math.min(scaleH, scaleW, 3)
}

/** Load document metadata to resolve the theme colour. */
async function loadDocInfo() {
  try {
    const data = await getDocument(props.documentId)
    theme = getTypeTheme(data.classification?.category)
  } catch {
    // Theme remains at default if document info fails to load.
  }
}

/**
 * Find the first page that contains a highlight.
 *
 * @returns The target page number (1-indexed).
 */
function findPageForChunk(): number {
  if (props.bbox && props.bbox.length > 0) {
    return props.bbox[0].page
  }
  return 1
}

/**
 * Render a PDF page onto the canvas with highlight overlays.
 *
 * @param pageNum - Page number to render (1-indexed).
 */
async function renderPage(pageNum: number) {
  if (!pdfDoc || !canvasRef.value || !containerRef.value) return
  const page = await pdfDoc.getPage(pageNum)
  const vp1 = page.getViewport({ scale: 1 })
  const s = computeFitScale(vp1.height, vp1.width)
  const viewport = page.getViewport({ scale: s })

  const canvas = canvasRef.value
  canvas.width = viewport.width
  canvas.height = viewport.height

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  await page.render({ canvasContext: ctx, viewport }).promise

  const pageBBoxes = highlightBBoxes.filter(b => b.page === pageNum)
  for (const b of pageBBoxes) {
    const x = b.x0 * s
    const y = b.y0 * s
    const w = (b.x1 - b.x0) * s
    const h = (b.y1 - b.y0) * s

    ctx.fillStyle = theme.color + '59'
    ctx.fillRect(x, y, w, h)
    ctx.strokeStyle = theme.color + '99'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, w, h)
  }
}

/** Re-render on window resize. */
function handleResize() {
  if (pdfDoc) {
    renderPage(currentPage.value)
  }
}

/** Load the PDF document and initialise state. */
async function loadPdf() {
  loading.value = true
  error.value = null
  try {
    const data = await getDocumentPdf(props.documentId)
    pdfDoc = await pdfjsLib.getDocument({ data }).promise
    totalPages.value = pdfDoc.numPages
    highlightBBoxes = props.bbox || []
    currentPage.value = findPageForChunk()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load PDF'
  } finally {
    loading.value = false
  }
  await nextTick()
  await renderPage(currentPage.value)
}

/**
 * Navigate to a specific page.
 *
 * @param pageNum - Target page number (1-indexed).
 */
async function goToPage(pageNum: number) {
  if (pageNum < 1 || pageNum > totalPages.value) return
  currentPage.value = pageNum
  await nextTick()
  await renderPage(pageNum)
}

// ── Lifecycle ──

onMounted(async () => {
  await loadDocInfo()
  await loadPdf()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
    @click.self="emit('close')"
  >
    <div class="bg-white border-[3px] border-black shadow-neo-lg max-w-5xl w-full mx-4 max-h-[90vh] flex flex-col">
      <!-- ── Modal header ────────────────────────────────────────── -->
      <div class="flex items-center justify-between px-5 py-3 shrink-0 border-b-[3px] border-black bg-white">
        <h3 class="font-bold text-sm uppercase tracking-wider">
          Document
          <span v-if="totalPages > 0" class="ml-2 font-bold text-gray-500 normal-case tracking-normal">
            Page {{ currentPage }} of {{ totalPages }}
          </span>
        </h3>
        <div class="flex items-center gap-2">
          <button
            class="neo-icon-btn"
            :disabled="currentPage <= 1"
            aria-label="Previous page"
            @click="goToPage(currentPage - 1)"
          >
            <ChevronLeft :size="13" />
          </button>
          <button
            class="neo-icon-btn"
            :disabled="currentPage >= totalPages"
            aria-label="Next page"
            @click="goToPage(currentPage + 1)"
          >
            <ChevronRight :size="13" />
          </button>
          <button
            class="w-8 h-8 flex items-center justify-center border-2 border-black btn-neo hover:btn-neo-pressed font-bold text-lg leading-none"
            @click="emit('close')"
          >
            &times;
          </button>
        </div>
      </div>

      <!-- ── PDF canvas area ─────────────────────────────────────── -->
      <div ref="containerRef" class="overflow-hidden p-4 flex-1 flex items-start justify-center bg-white border-t-[3px] border-black">
        <div v-if="loading" class="py-12 text-gray-400 font-bold">Loading PDF...</div>
        <div v-else-if="error" class="py-12 text-red-600 font-bold">{{ error }}</div>
        <canvas v-else ref="canvasRef" class="shadow-neo shrink-0" />
      </div>

      <!-- ── Page navigation ─────────────────────────────────────── -->
      <div v-if="totalPages > 0" class="flex items-center justify-center gap-2 px-5 py-2 text-xs font-bold shrink-0 border-t-[3px] border-black bg-white">
        <span>Page</span>
        <input
          type="number"
          :value="currentPage"
          :min="1"
          :max="totalPages"
          class="w-16 text-center input-neo focus:input-neo-focus px-2 py-1 text-gray-700"
          @change="goToPage(Number(($event.target as HTMLInputElement).value))"
        />
        <span>of {{ totalPages }}</span>
      </div>
    </div>
  </div>
</template>
