/**
 * Chat session store.
 *
 * Manages chat messages, loading state, and document info for the Q&A
 * interface on a single document.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDocument } from '../api/documents'
import { getChatHistory, postChatMessage } from '../api/chat'
import type { SourceChunk } from '../api/chat'

// ── Types ──────────────────────────────────────────────────────────

/** A field value extracted during document classification with its source location. */
export interface ExtractedField {
  /** The extracted value as a string. */
  value: string | null
  /** Index of the chunk that contained this value. */
  chunk_index: number | null
  /** Database id of the chunk (resolved after ingestion). */
  chunk_id: number | null
  /** Page numbers where the value appears. */
  page_numbers: number[]
  /** Bounding boxes for visual highlighting. */
  bbox: { page: number; x0: number; y0: number; x1: number; y1: number }[]
}

/** Summary information about the current document. */
export interface DocumentInfo {
  /** Document UUID. */
  document_id: string
  /** Classification result with category, confidence, reasoning. */
  classification: { category: string; confidence: number; reasoning: string }
  /** Number of ingested chunks. */
  chunk_count: number
  /** Auto-extracted title. */
  title: string | null
  /** Auto-extracted summary. */
  summary: string | null
  /** Category-specific extracted fields. */
  extractions: Record<string, ExtractedField> | null
}

/** A single message in the chat UI. */
export interface ChatMessage {
  /** Message sender. */
  role: 'user' | 'assistant'
  /** Message body text. */
  content: string
  /** Source chunks cited by the assistant (empty for user messages). */
  source_chunks?: SourceChunk[]
}

// ── Store ──────────────────────────────────────────────────────────

/**
 * Pinia store for chat interactions with a single document.
 *
 * @returns Reactive state and action methods for Q&A.
 */
export const useChatStore = defineStore('chat', () => {
  // ── State ────────────────────────────────────────────────────────

  /** Ordered list of chat messages. */
  const messages = ref<ChatMessage[]>([])
  /** True while waiting for an assistant response. */
  const loading = ref(false)
  /** Most recent error message, or null. */
  const error = ref<string | null>(null)
  /** Cached document info for the current chat session. */
  const documentInfo = ref<DocumentInfo | null>(null)

  // ── Actions ──────────────────────────────────────────────────────

  /**
   * Fetch document metadata and cache it in the store.
   *
   * @param documentId - Document UUID.
   */
  async function loadDocumentInfo(documentId: string) {
    try {
      documentInfo.value = await getDocument(documentId) as unknown as DocumentInfo
    } catch {
      // Silently ignored; the chat page can degrade gracefully.
    }
  }

  /**
   * Load previous chat history for the given document.
   *
   * Resets the local messages array to the server-side history.
   *
   * @param documentId - Document UUID.
   */
  async function loadHistory(documentId: string) {
    messages.value = []
    try {
      const { messages: raw } = await getChatHistory(documentId)
      messages.value = raw.map(m => ({
        role: m.role,
        content: m.content,
        source_chunks: m.source_chunks || [],
      }))
    } catch {
      // Silently ignored; history is non-critical.
    }
  }

  /**
   * Send a user question and append the assistant's response to the
   * message list.
   *
   * @param documentId - Document UUID.
   * @param question   - The user's question text.
   */
  async function send(documentId: string, question: string) {
    messages.value.push({ role: 'user', content: question })
    loading.value = true
    error.value = null

    try {
      const data = await postChatMessage(documentId, question)
      messages.value.push({
        role: 'assistant',
        content: data.answer,
        source_chunks: data.source_chunks || [],
      })
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Chat failed'
    } finally {
      loading.value = false
    }
  }

  return { messages, loading, error, documentInfo, send, loadHistory, loadDocumentInfo }
})
