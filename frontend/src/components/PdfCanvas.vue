<script lang="ts">
/**
 * PDF page renderer with highlight overlays.
 *
 * Renders a single PDF page onto an HTML canvas and draws bounding-box
 * highlights on top. Watches prop changes to re-render automatically.
 * Previous render tasks are cancelled before starting new ones to avoid
 * pdfjs "multiple render operations" errors.
 *
 * @displayName PdfCanvas
 * @version 1.0.0
 * @example
 * ```vue
 * <PdfCanvas
 *   :pdf-doc="pdfDoc"
 *   :current-page="1"
 *   :highlight-b-boxes="bboxes"
 *   theme-color="#2563eb"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'

/** A bounding-box rectangle on a PDF page. */
interface BBox {
  /** 1-indexed page number. */
  page: number
  /** Left edge in PDF points. */
  x0: number
  /** Top edge in PDF points. */
  y0: number
  /** Right edge in PDF points. */
  x1: number
  /** Bottom edge in PDF points. */
  y1: number
}

/** Minimal pdfjs page proxy interface used by this component. */
interface PDFPage {
  getViewport(options: { scale: number }): { height: number; width: number }
  render(options: { canvasContext: CanvasRenderingContext2D; viewport: unknown }): { promise: Promise<void>; cancel: () => void }
}

/** Minimal pdfjs document proxy interface used by this component. */
interface PDFDocument {
  numPages: number
  getPage(pageNum: number): Promise<PDFPage>
}

/** Padding around the canvas inside its container (px). */
const PADDING = 32

const props = defineProps<{
  /** The loaded pdfjs document proxy. */
  pdfDoc: PDFDocument
  /** Current page number to render (1-indexed). */
  currentPage: number
  /** Bounding boxes to highlight on the rendered page. */
  highlightBBoxes: BBox[]
  /** Hex colour string for highlight fill and stroke. */
  themeColor: string
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)

/** Reference to the current pdfjs render task for cancellation. */
let renderTask: { cancel: () => void; promise: Promise<void> } | null = null
/** Debounce flag to collapse rapid watcher firings into a single render. */
let renderPending = false

/**
 * Compute the scale factor so that the page fits within the container
 * while respecting the maximum scale of 3.
 *
 * @param pageHeight - Full page height at 1x scale.
 * @param pageWidth  - Full page width at 1x scale.
 * @returns The scale factor to apply.
 */
function computeFitScale(pageHeight: number, pageWidth: number): number {
  if (!containerRef.value) return 1
  const cw = containerRef.value.clientWidth - PADDING
  if (cw <= 0) return 1
  const scaleW = cw / pageWidth
  const ch = containerRef.value.clientHeight - PADDING
  if (ch <= 0) return 1
  const scaleH = ch / pageHeight
  return Math.min(scaleH, scaleW, 3)
}

/**
 * Render the given page onto the canvas and draw any highlights.
 *
 * Cancels any in-progress render before starting. This is required
 * because pdfjs does not allow concurrent render operations on the
 * same canvas element.
 *
 * @param pageNum - Page number to render (1-indexed).
 */
async function renderPage(pageNum: number) {
  if (!props.pdfDoc || !canvasRef.value || !containerRef.value) return

  // Cancel any previous render before starting a new one.
  if (renderTask) {
    renderTask.cancel()
    renderTask = null
  }

  const page = await props.pdfDoc.getPage(pageNum)
  const vp1 = page.getViewport({ scale: 1 })
  const s = computeFitScale(vp1.height, vp1.width)
  const viewport = page.getViewport({ scale: s })

  const canvas = canvasRef.value
  if (!canvas) return
  canvas.width = viewport.width
  canvas.height = viewport.height

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  renderTask = page.render({ canvasContext: ctx, viewport })
  await renderTask.promise
  renderTask = null

  // Draw highlight overlays.
  const pageBBoxes = props.highlightBBoxes.filter(b => b.page === pageNum)
  for (const b of pageBBoxes) {
    const x = b.x0 * s
    const y = b.y0 * s
    const w = (b.x1 - b.x0) * s
    const h = (b.y1 - b.y0) * s
    ctx.fillStyle = props.themeColor + '59'
    ctx.fillRect(x, y, w, h)
    ctx.strokeStyle = props.themeColor + '99'
    ctx.lineWidth = 2
    ctx.strokeRect(x, y, w, h)
  }
}

/**
 * Debounced render scheduler.
 *
 * Collapses multiple synchronous prop changes (e.g. page + bbox + theme
 * changing in the same tick) into a single render call via nextTick.
 */
function scheduleRender() {
  if (renderPending) return
  renderPending = true
  nextTick(async () => {
    renderPending = false
    await renderPage(props.currentPage)
  })
}

/** Re-render on window resize. */
function handleResize() {
  if (props.pdfDoc) {
    scheduleRender()
  }
}

// ── Watchers ──────────────────────────────────────────────────────────

watch(() => props.currentPage, () => { scheduleRender() })
watch(() => props.highlightBBoxes, () => { scheduleRender() }, { deep: true })
watch(() => props.themeColor, () => { scheduleRender() })

// ── Lifecycle ─────────────────────────────────────────────────────────

onMounted(async () => {
  await nextTick()
  if (props.pdfDoc) {
    await renderPage(props.currentPage)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (renderTask) {
    renderTask.cancel()
    renderTask = null
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <!-- ── Canvas container ────────────────────────────────────────── -->
  <div ref="containerRef" class="flex-1 flex items-start justify-center p-4 bg-white overflow-hidden">
    <canvas ref="canvasRef" class="shadow-neo shrink-0" />
  </div>
</template>
