/**
 * Document management store.
 *
 * Centralises all document CRUD state and actions so that any component
 * can access the document list, upload progress, and error state without
 * duplicating logic.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../api/documents'
import type { DocumentListItem, DocumentResponse } from '../api/documents'

/**
 * Pinia store responsible for managing the document grid.
 *
 * @returns An object containing reactive state and action methods.
 */
export const useDocumentStore = defineStore('document', () => {
  // ── State ────────────────────────────────────────────────────────

  /** Sorted list of ready documents (newest first). */
  const documents = ref<DocumentListItem[]>([])
  /** True while a fetch-all request is in flight. */
  const loading = ref(false)
  /** True while a file upload is in progress. */
  const uploading = ref(false)
  /** Most recent error message, or null. */
  const error = ref<string | null>(null)

  // ── Actions ──────────────────────────────────────────────────────

  /**
   * Fetch all ready documents from the server.
   *
   * Updates `documents`, `loading`, and `error` reactively.
   */
  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      documents.value = await api.listDocuments()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch documents'
    } finally {
      loading.value = false
    }
  }

  /**
   * Upload a PDF file, then refresh the document list.
   *
   * @param file - The PDF File to upload.
   * @returns The created document response, or null on failure.
   */
  async function upload(file: File): Promise<DocumentResponse | null> {
    uploading.value = true
    error.value = null
    try {
      const result = await api.uploadDocument(file)
      await fetchAll()
      return result
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Upload failed'
      return null
    } finally {
      uploading.value = false
    }
  }

  /**
   * Rename a document and refresh the list.
   *
   * @param id       - Document UUID.
   * @param filename - New filename.
   * @returns True on success, false on failure.
   */
  async function rename(id: string, filename: string): Promise<boolean> {
    error.value = null
    try {
      await api.renameDocument(id, filename)
      await fetchAll()
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Rename failed'
      return false
    }
  }

  /**
   * Delete a document and optimistically remove it from the local list.
   *
   * @param id - Document UUID.
   * @returns True on success, false on failure.
   */
  async function remove(id: string): Promise<boolean> {
    error.value = null
    try {
      await api.deleteDocument(id)
      documents.value = documents.value.filter(d => d.document_id !== id)
      return true
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Delete failed'
      return false
    }
  }

  return { documents, loading, uploading, error, fetchAll, upload, rename, remove }
})
