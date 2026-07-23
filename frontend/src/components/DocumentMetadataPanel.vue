<script lang="ts">
/**
 * Document metadata panel.
 *
 * Shows the document title, summary, and extracted fields organised by
 * section groups defined in `extractionFields`. Field values with a
 * source location can be clicked to emit a `jump-to-field` event.
 *
 * @displayName DocumentMetadataPanel
 * @version 1.0.0
 * @example
 * ```vue
 * <DocumentMetadataPanel
 *   :extractions="extractions"
 *   doc-title="RFP Document"
 *   doc-summary="A summary..."
 *   theme-color="#2563eb"
 *   @view-pdf="showPdf"
 *   @jump-to-field="jumpToField"
 * />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { fieldLabels, sectionGroups } from '../constants/extractionFields'

// ── Types ──

/** Bounding-box rectangle for a PDF highlight. */
interface BBox {
  page: number
  x0: number
  y0: number
  x1: number
  y1: number
}

/** An extracted field with its source location metadata. */
interface ExtractedField {
  value: string | null
  chunk_id: number | null
  bbox: BBox[]
}

// ── Props ──

const props = defineProps<{
  /** Category-specific extracted fields keyed by field name. */
  extractions: Record<string, ExtractedField> | null
  /** Auto-extracted document title. */
  docTitle: string | null
  /** Auto-extracted one-paragraph summary. */
  docSummary: string | null
  /** Theme colour for UI accents. */
  themeColor: string
}>()

// ── Emits ──

const emit = defineEmits<{
  /** User wants to switch from metadata to PDF view. */
  (e: 'view-pdf'): void
  /** User clicked an extracted field to jump to its source. */
  (e: 'jump-to-field', field: { chunk_id: number | null; bbox: BBox[] }): void
}>()

// ── Methods ──

/**
 * Build a flat list of non-null extraction field entries.
 *
 * @returns Array of field data objects with key, label, value, and
 *   source location info.
 */
function fieldEntries(): { key: string; label: string; value: string; chunk_id: number | null; bbox: BBox[] }[] {
  if (!props.extractions) return []
  const result: { key: string; label: string; value: string; chunk_id: number | null; bbox: BBox[] }[] = []
  for (const [key, field] of Object.entries(props.extractions)) {
    if (field.value != null) {
      result.push({ key, label: fieldLabels[key] || key, value: field.value, chunk_id: field.chunk_id, bbox: field.bbox })
    }
  }
  return result
}

/**
 * Emit a jump-to-field event for the clicked field.
 *
 * @param field - The field's source location data.
 */
function jumpToField(field: { chunk_id: number | null; bbox: BBox[] }) {
  emit('jump-to-field', field)
}
</script>

<template>
  <div class="w-full h-full overflow-y-auto bg-white border-[3px] border-black shadow-neo p-6 rounded-none">
    <!-- ── Title ────────────────────────────────────────────────── -->
    <h1 class="text-xl font-bold text-gray-900 mb-3">{{ docTitle }}</h1>

    <!-- ── Summary ──────────────────────────────────────────────── -->
    <p v-if="docSummary" class="text-sm text-gray-600 leading-relaxed mb-6">{{ docSummary }}</p>

    <!-- ── View PDF button ──────────────────────────────────────── -->
    <button
      class="mb-6 inline-flex items-center gap-2 px-4 py-2 text-sm font-bold uppercase border-2 border-black btn-neo hover:btn-neo-pressed text-white"
      :style="{ backgroundColor: themeColor }"
      @click="emit('view-pdf')"
    >
      <span>View PDF</span>
      <span>&rarr;</span>
    </button>

    <!-- ── Section groups ───────────────────────────────────────── -->
    <div class="space-y-5">
      <template v-for="group in sectionGroups" :key="group.label">
        <div v-if="fieldEntries().filter(f => group.keys.includes(f.key)).length > 0">
          <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">{{ group.label }}</h3>
          <div class="space-y-1.5">
            <div
              v-for="f in fieldEntries().filter(f => group.keys.includes(f.key))"
              :key="f.key"
              class="text-sm text-gray-700 cursor-pointer hover:text-gray-900 transition-colors"
              @click="f.chunk_id != null ? jumpToField(f) : undefined"
            >
              <span class="font-bold">{{ f.label }}:</span>
              <span class="ml-1">{{ f.value }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
