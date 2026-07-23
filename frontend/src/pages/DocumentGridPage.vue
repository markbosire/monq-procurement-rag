<script lang="ts">
/**
 * Document grid page.
 *
 * Displays all uploaded documents in a responsive grid with context
 * menus for renaming and deleting. Also handles file uploads via a
 * button click or drag-and-drop with a processing status card.
 *
 * @displayName DocumentGridPage
 * @version 1.0.0
 * @example
 * ```vue
 * <DocumentGridPage />
 * ```
 */
export {}
</script>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { MoreVertical, Trash2, Pencil, Upload, AlertCircle } from 'lucide-vue-next'
import { getTypeTheme } from '../constants/documentTypeTheme'
import type { TypeTheme } from '../constants/documentTypeTheme'
import { useDocumentStore } from '../stores/useDocumentStore'
import { useToast } from '../composables/useToast'
import RenameDocumentModal from '../components/RenameDocumentModal.vue'
import DeleteConfirmModal from '../components/DeleteConfirmModal.vue'

// ── Types ──

/** A document item as returned by the API. */
interface DocItem {
  document_id: string
  filename: string
  category: string | null
  chunk_count: number
  title: string | null
  created_at: string | null
}

/** A processing document card shown during upload. */
interface ProcessingCard {
  filename: string
  status: 'uploading' | 'processing' | 'error'
  error?: string
  category?: string
}

// ── State ──

const router = useRouter()
const store = useDocumentStore()
const { show: showToast } = useToast()
const dragOver = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const processingCard = ref<ProcessingCard | null>(null)

const menuDocId = ref<string | null>(null)
const deleteConfirmId = ref<string | null>(null)
const renameDocId = ref<string | null>(null)

// ── Lifecycle ──

onMounted(() => store.fetchAll())

// ── Methods ──

/** Toggle the context menu for a document card. */
function toggleMenu(docId: string) {
  menuDocId.value = menuDocId.value === docId ? null : docId
}

/** Close all open context menus. */
function closeMenu() {
  menuDocId.value = null
}

/** Open the rename modal for a document. */
function startRename(doc: DocItem) {
  renameDocId.value = doc.document_id
  menuDocId.value = null
}

/**
 * Confirm a rename operation.
 *
 * @param docId - UUID of the document to rename.
 * @param name  - New filename.
 */
async function confirmRename(docId: string, name: string) {
  const ok = await store.rename(docId, name)
  if (ok) {
    renameDocId.value = null
  } else {
    showToast(store.error || 'Failed to rename document')
  }
}

/** Open the delete confirmation for a document. */
function startDelete(docId: string) {
  deleteConfirmId.value = docId
  menuDocId.value = null
}

/** Confirm deletion of the selected document. */
async function confirmDelete() {
  if (!deleteConfirmId.value) return
  const ok = await store.remove(deleteConfirmId.value)
  if (!ok) {
    showToast(store.error || 'Failed to delete document')
  }
  deleteConfirmId.value = null
}

/** Navigate to the chat page for a document. */
function openDocument(id: string) {
  router.push(`/documents/${id}`)
}

/** Resolve the visual theme for a document's category. */
function themeFor(doc: DocItem): TypeTheme {
  return getTypeTheme(doc.category)
}

/** Format an ISO date string for display. */
function formatDate(iso: string | null): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString()
}

/**
 * Upload a PDF file and show a processing card.
 *
 * @param file - The PDF file to upload.
 */
async function uploadFile(file: File) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('Please select a PDF file')
    return
  }
  processingCard.value = { filename: file.name, status: 'uploading' }
  const result = await store.upload(file)
  if (result) {
    processingCard.value = {
      filename: file.name,
      status: 'processing',
      category: result.classification?.category,
    }
    await new Promise(r => setTimeout(r, 1200))
    processingCard.value = null
  } else {
    processingCard.value = { filename: file.name, status: 'error', error: store.error || 'Upload failed' }
  }
}

/** Handle file selected via the hidden input element. */
function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadFile(file)
  input.value = ''
}

/** Handle a file dropped onto the drop zone. */
function onDrop(event: DragEvent) {
  event.preventDefault()
  dragOver.value = false
  const file = event.dataTransfer?.files[0]
  if (!file) return
  uploadFile(file)
}

/** Mark drag-over state for visual feedback. */
function onDragOver(event: DragEvent) {
  event.preventDefault()
  dragOver.value = true
}

/** Clear drag-over state when the user leaves the drop zone. */
function onDragLeave() {
  dragOver.value = false
}
</script>

<template>
  <div
    class="min-h-screen"
    @drop="onDrop"
    @dragover="onDragOver"
    @dragleave="onDragLeave"
    @click="closeMenu"
  >
    <main class="max-w-7xl mx-auto p-6 lg:p-10">
      <!-- ── Page header ─────────────────────────────────────────── -->
      <div class="page-head flex items-end justify-between gap-6 flex-wrap mb-5">
        <h1 class="font-display text-[46px] leading-[0.9] tracking-tight relative inline-block">
          DOCUMENTS
          <span class="absolute left-[2px] right-[2px] bottom-[-10px] h-[10px] bg-black -skew-x-[12deg]" />
        </h1>
        <div class="font-mono text-xs uppercase tracking-widest text-[#3a3a3a] bg-white border-[3px] border-black px-3.5 py-2 shadow-neo-sm">
          {{ store.documents.length }} file{{ store.documents.length !== 1 ? 's' : '' }} &middot; procurement RAG
        </div>
      </div>

      <!-- ── Loading state ───────────────────────────────────────── -->
      <div v-if="store.loading && store.documents.length === 0" class="text-gray-500 text-center py-12 font-bold">
        Loading...
      </div>

      <!-- ── Document grid ───────────────────────────────────────── -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-[30px]">
        <!-- ── Add card ───────────────────────────────────────────── -->
        <div
          v-if="!processingCard"
          class="neo-add-card min-h-[230px] flex flex-col items-center justify-center gap-[10px] p-5"
          @click="fileInput?.click()"
        >
          <div class="neo-plus-box font-display text-2xl">+</div>
          <span class="font-display text-sm tracking-wider uppercase">Add Document</span>
          <span class="font-mono text-xs text-[#6b6b6b]">or drag a PDF here</span>
        </div>

        <!-- ── Processing card ───────────────────────────────────── -->
        <div
          v-if="processingCard"
          class="border-[3px] border-black overflow-hidden bg-white shadow-neo min-h-[230px] flex flex-col"
        >
          <div
            class="flex-1 flex items-center justify-center"
            :class="{
              'bg-[#2563eb] text-white': processingCard.status === 'uploading',
              'bg-[#7c3aed] text-white': processingCard.status === 'processing',
              'bg-[#dc2626] text-white': processingCard.status === 'error',
            }"
          >
            <component
              :is="processingCard.status === 'error' ? AlertCircle : Upload"
              :size="40"
              :stroke-width="2"
            />
          </div>
          <div class="p-4 flex-1 flex flex-col justify-center border-t-[3px] border-black">
            <p class="text-sm font-bold line-clamp-2">{{ processingCard.filename }}</p>
            <p v-if="processingCard.status === 'uploading'" class="text-xs mt-2">
              <span class="inline-flex items-center gap-1.5">
                <span class="w-3 h-3 bg-black animate-pulse" />
                Uploading&hellip;
              </span>
            </p>
            <p v-else-if="processingCard.status === 'processing'" class="text-xs mt-2">
              <span class="inline-flex items-center gap-1.5">
                <span class="w-3 h-3 bg-black animate-pulse" />
                Parsing, chunking &amp; classifying&hellip;
              </span>
            </p>
            <p v-else-if="processingCard.status === 'error'" class="text-xs font-bold text-red-600 mt-2">
              {{ processingCard.error || 'Upload failed' }}
            </p>
          </div>
        </div>

        <!-- ── Document cards ────────────────────────────────────── -->
        <div
          v-for="doc in store.documents"
          :key="doc.document_id"
          class="neo-card min-h-[230px] p-5 flex flex-col gap-[14px] cursor-pointer"
          :style="{ '--neo-shadow': themeFor(doc).color }"
          @click="openDocument(doc.document_id)"
        >
          <div class="card-top flex items-start justify-between">
            <div
              class="neo-icon-block"
              :style="{ backgroundColor: themeFor(doc).color, color: '#fff' }"
            >
              <component :is="themeFor(doc).icon" :size="24" :stroke-width="2" />
            </div>
            <div class="relative">
              <div class="neo-menu-btn" @click.stop="toggleMenu(doc.document_id)">
                <MoreVertical :size="16" />
              </div>
              <div
                v-if="menuDocId === doc.document_id"
                class="absolute top-10 right-0 bg-white border-2 border-black shadow-neo-sm z-10 w-36 py-1"
                @click.stop
              >
                <button
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm font-bold hover:bg-gray-100"
                  @click="startRename(doc)"
                >
                  <Pencil :size="14" />
                  Rename
                </button>
                <button
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm font-bold text-red-600 hover:bg-red-100"
                  @click="startDelete(doc.document_id)"
                >
                  <Trash2 :size="14" />
                  Delete
                </button>
              </div>
            </div>
          </div>

          <!-- ── Rename modal inline ─────────────────────────────── -->
          <template v-if="renameDocId === doc.document_id">
            <RenameDocumentModal
              :model-value="renameDocId === doc.document_id"
              :initial-name="doc.filename"
              @update:model-value="renameDocId = null"
              @confirm="(name) => confirmRename(doc.document_id, name)"
            />
          </template>
          <template v-else>
            <p class="font-bold text-base leading-snug line-clamp-2">{{ doc.filename }}</p>
            <div v-if="doc.category" class="flex">
              <span class="neo-badge" :style="{ backgroundColor: themeFor(doc).color }">
                {{ doc.category }}
              </span>
            </div>
            <span v-else class="text-xs text-gray-400 font-mono uppercase tracking-wider">Unclassified</span>
            <!-- ── Card footer metadata ───────────────────────────── -->
            <div class="neo-card-footer pt-[10px] mt-auto flex items-center gap-2 font-mono text-xs text-[#4a4a4a]">
              <span>{{ doc.chunk_count }} chunks</span>
              <span class="text-[#b9b3a4]">&middot;</span>
              <span>{{ formatDate(doc.created_at) }}</span>
            </div>
          </template>
        </div>
      </div>

      <!-- ── Hidden file input ───────────────────────────────────── -->
      <input ref="fileInput" type="file" accept=".pdf" class="hidden" @change="onFileSelected" />

      <!-- ── Drag-over overlay ───────────────────────────────────── -->
      <div
        v-if="dragOver"
        class="fixed inset-0 z-40 flex items-center justify-center pointer-events-none"
      >
        <div class="border-[6px] border-dashed border-black bg-white w-[90vw] h-[80vh] flex items-center justify-center shadow-neo-lg">
          <p class="text-2xl font-black uppercase tracking-wider">Drop PDF here</p>
        </div>
      </div>

      <DeleteConfirmModal
        :model-value="deleteConfirmId !== null"
        @update:model-value="deleteConfirmId = null"
        @confirm="confirmDelete"
      />
    </main>
  </div>
</template>
