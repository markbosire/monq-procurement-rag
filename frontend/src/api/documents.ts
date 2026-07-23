/**
 * Document API helpers.
 *
 * Provides typed functions for every document-related backend endpoint:
 * listing, fetching, uploading, renaming, deleting, and PDF retrieval.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { apiFetch, apiFetchRaw } from './apiClient'

// ── Types ──────────────────────────────────────────────────────────

/** A lightweight summary of a document shown in the document grid. */
export interface DocumentListItem {
  /** UUID of the document. */
  document_id: string
  /** Uploaded file name. */
  filename: string
  /** Classified procurement category (e.g. "Contract", "RFP/RFQ"). */
  category: string | null
  /** Number of text chunks produced during ingestion. */
  chunk_count: number
  /** Auto-extracted document title, if any. */
  title: string | null
  /** ISO-8601 creation timestamp. */
  created_at: string | null
}

/** Classification result attached to every document. */
export interface ClassificationResult {
  /** Predicted category label. */
  category: string
  /** Confidence score in [0, 1]. */
  confidence: number
  /** Natural-language explanation from the classifier. */
  reasoning: string
}

/** Full document details returned by single-document endpoints. */
export interface DocumentResponse {
  /** UUID of the document. */
  document_id: string
  /** Classification result. */
  classification: ClassificationResult
  /** Number of text chunks. */
  chunk_count: number
  /** Processing status (e.g. "ready", "processing"). */
  status: string
  /** If set, this document is a duplicate of the referenced id. */
  duplicate_of?: string
  /** Auto-extracted document title. */
  title: string | null
  /** Auto-extracted document summary. */
  summary: string | null
  /** Category-specific extracted fields (e.g. parties, effective_date). */
  extractions: Record<string, unknown> | null
}

// ── Endpoints ──────────────────────────────────────────────────────

/**
 * Fetch the full list of ready documents, newest first.
 *
 * @returns Promise resolving to an array of document list items.
 * @throws {ApiError} On request failure.
 */
export async function listDocuments(): Promise<DocumentListItem[]> {
  return apiFetch<DocumentListItem[]>('/api/documents')
}

/**
 * Fetch full details for a single document.
 *
 * @param id - Document UUID.
 * @returns Promise resolving to the document response.
 * @throws {ApiError} If the document is not found.
 */
export async function getDocument(id: string): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>(`/api/documents/${id}`)
}

/**
 * Upload a PDF file for ingestion.
 *
 * @param file - The PDF File object to upload.
 * @returns Promise resolving to the created document response.
 * @throws {ApiError} On validation or processing errors.
 */
export async function uploadDocument(file: File): Promise<DocumentResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch<DocumentResponse>('/api/documents', { method: 'POST', body: formData })
}

/**
 * Rename (re-filename) an existing document.
 *
 * @param id       - Document UUID.
 * @param filename - New filename (must not be empty).
 * @returns Promise resolving to the updated document response.
 * @throws {ApiError} If the document is not found or validation fails.
 */
export async function renameDocument(id: string, filename: string): Promise<DocumentResponse> {
  return apiFetch<DocumentResponse>(`/api/documents/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename }),
  })
}

/**
 * Delete a document and all associated chunks / chat history.
 *
 * @param id - Document UUID.
 * @throws {ApiError} If the document is not found.
 */
export async function deleteDocument(id: string): Promise<void> {
  await apiFetchRaw(`/api/documents/${id}`, { method: 'DELETE' })
}

/**
 * Retrieve the raw PDF binary for a document.
 *
 * @param id - Document UUID.
 * @returns Promise resolving to an ArrayBuffer of the PDF content.
 * @throws {ApiError} If the PDF is not available.
 */
export async function getDocumentPdf(id: string): Promise<ArrayBuffer> {
  const res = await apiFetchRaw(`/api/documents/${id}/pdf`)
  return res.arrayBuffer()
}
