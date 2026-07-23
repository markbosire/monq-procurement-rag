<script lang="ts">
/**
 * Document viewer panel.
 *
 * Orchestrates the PDF canvas, metadata panel, and navigation toolbar.
 * Manages the active highlight state from the source viewer composable
 * and toggles between the metadata and PDF views.
 *
 * @displayName DocumentViewerPanel
 * @version 1.0.0
 * @example
 * ```vue
 * <DocumentViewerPanel document-id="uuid" />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as pdfjsLib from 'pdfjs-dist'
import { activeHighlight } from '../composables/useSourceViewer'
import { getTypeTheme } from '../constants/documentTypeTheme'
import type { TypeTheme } from '../constants/documentTypeTheme'
import { getDocument, getDocumentPdf } from '../api/documents'
import PdfToolbar from './PdfToolbar.vue'
import PdfCanvas from './PdfCanvas.vue'
import MetadataPanel from './MetadataPanel.vue'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

/** Bounding-box rectangle for PDF highlights. */
interface BBox {
  page: number
  x0: number
  y0: number
  x1: number
  y1: number
}

/** An extracted field with source location. */
interface ExtractedField {
  value: string | null
  chunk_id: number | null
  bbox: BBox[]
}

const props = defineProps<{
  /** UUID of the document to display. */
  documentId: string
}>()

// ── State ──────────────────────────────────────────────────────────────

const currentPage = ref(1)
const totalPdfPages = ref(0)
const loading = ref(true)
const error = ref<string | null>(null)
const docCategory = ref<string | null>(null)
const docTitle = ref<string | null>(null)
const docSummary = ref<string | null>(null)
const extractions = ref<Record<string, ExtractedField> | null>(null)
const viewingMetadata = ref(true)

/** Loaded pdfjs document proxy. */
let pdfDoc: pdfjsLib.PDFDocumentProxy | null = null
/** Bounding boxes for the currently active highlight. */
const currentHighlightBBoxes = ref<BBox[]>([])
/** Resolved theme for the document category. */
const currentTheme = ref<TypeTheme>(getTypeTheme(null))

// ── Computed ───────────────────────────────────────────────────────────

const hasMetadata = computed(() => {
  if (!extractions.value) return false
  return Object.values(extractions.value).some((f: ExtractedField) => f.value != null)
})

// ── Methods ────────────────────────────────────────────────────────────

/** Load document metadata (title, summary, extractions). */
async function loadDocInfo() {
  try {
    const data = await getDocument(props.documentId)
    docTitle.value = data.title
    docSummary.value = data.summary
    docCategory.value = data.classification?.category ?? null
    currentTheme.value = getTypeTheme(docCategory.value)
    extractions.value = data.extractions as Record<string, ExtractedField> | null
  } catch {
    // Silently ignored; the PDF view still works.
  }
}

/**
 * Navigate to the source location of a metadata field.
 *
 * Switches to PDF view and sets the active highlight.
 *
 * @param field - Field with bbox and chunk_id for the target location.
 */
function jumpToField(field: { chunk_id: number | null; bbox: BBox[] }) {
  if (!field.bbox || field.bbox.length === 0 || field.chunk_id == null) return
  viewingMetadata.value = false
  const targetPage = field.bbox[0].page
  nextTick(async () => {
    if (pdfDoc) {
      if (targetPage !== currentPage.value) {
        currentPage.value = targetPage
      }
      activeHighlight.value = { chunkId: field.chunk_id!, bbox: field.bbox }
    }
  })
}

/** Stub resize handler; actual rendering is driven by PdfCanvas watchers. */
function handleResize() {
  // Render handled by PdfCanvas watchers
}

/** Load the PDF document binary and initialise pdfjs. */
async function loadPdf() {
  loading.value = true
  error.value = null
  try {
    const data = await getDocumentPdf(props.documentId)
    pdfDoc = await pdfjsLib.getDocument({ data }).promise
    totalPdfPages.value = pdfDoc.numPages
    currentPage.value = 1
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Failed to load PDF'
  } finally {
    loading.value = false
  }
}

/**
 * Navigate to a specific PDF page.
 *
 * @param pageNum - Target page number (1-indexed).
 */
function goToPage(pageNum: number) {
  if (pageNum < 1 || pageNum > totalPdfPages.value) return
  currentPage.value = pageNum
  viewingMetadata.value = false
}

/**
 * Process a new active highlight from the source viewer.
 *
 * Updates the highlight bboxes and navigates to the target page.
 *
 * @param hl - The highlight data (or null to clear).
 */
function handleActiveHighlight(hl: { chunkId: number; bbox: BBox[] } | null) {
  if (!hl || !hl.bbox || hl.bbox.length === 0) {
    currentHighlightBBoxes.value = []
    viewingMetadata.value = false
    return
  }
  currentHighlightBBoxes.value = hl.bbox
  const targetPage = hl.bbox[0].page
  viewingMetadata.value = false
  if (targetPage !== currentPage.value) {
    currentPage.value = targetPage
  }
}

// ── Watchers ───────────────────────────────────────────────────────────

watch(activeHighlight, async (hl) => {
  if (!pdfDoc) return
  handleActiveHighlight(hl)
})

watch(viewingMetadata, async (v) => {
  if (!v && pdfDoc) {
    await nextTick()
  }
})

// ── Lifecycle ──────────────────────────────────────────────────────────

onMounted(async () => {
  await Promise.all([loadPdf(), loadDocInfo()])
  if (activeHighlight.value) {
    handleActiveHighlight(activeHighlight.value)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="flex flex-col h-full bg-white border-l-[3px] border-t-[3px] border-black">
    <!-- ── Navigation toolbar ────────────────────────────────────── -->
    <PdfToolbar
      :current-page="currentPage"
      :total-pages="totalPdfPages"
      :viewing-metadata="viewingMetadata"
      :has-metadata="hasMetadata"
      :doc-title="docTitle"
      @go-to-page="goToPage"
      @toggle-metadata="viewingMetadata = !viewingMetadata"
    />

    <!-- ── Loading state ─────────────────────────────────────────── -->
    <div v-if="loading" class="flex-1 flex items-center justify-center py-12 text-gray-400 font-bold">
      Loading PDF...
    </div>

    <!-- ── Error state ───────────────────────────────────────────── -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center py-12 text-red-600 font-bold">
      {{ error }}
    </div>

    <!-- ── Metadata panel ────────────────────────────────────────── -->
    <MetadataPanel
      v-else-if="viewingMetadata && (docTitle || hasMetadata)"
      :extractions="extractions"
      :doc-title="docTitle"
      :doc-summary="docSummary"
      :theme-color="currentTheme.color"
      @view-pdf="viewingMetadata = false"
      @jump-to-field="jumpToField"
    />

    <!-- ── PDF canvas ────────────────────────────────────────────── -->
    <PdfCanvas
      v-else-if="!viewingMetadata && pdfDoc"
      :pdf-doc="pdfDoc"
      :current-page="currentPage"
      :highlight-b-boxes="currentHighlightBBoxes"
      :theme-color="currentTheme.color"
    />
  </div>
</template>
