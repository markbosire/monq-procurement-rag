/**
 * Chat API helpers.
 *
 * Provides typed functions for chat-history retrieval and sending new
 * messages to a document's Q&A endpoint.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { apiFetch } from './apiClient'

// ── Types ──────────────────────────────────────────────────────────

/** A bounding-box rectangle on a PDF page used for source highlighting. */
export interface BBox {
  /** 1-indexed page number. */
  page: number
  /** Left edge of the rectangle in PDF points. */
  x0: number
  /** Top edge of the rectangle in PDF points. */
  y0: number
  /** Right edge of the rectangle in PDF points. */
  x1: number
  /** Bottom edge of the rectangle in PDF points. */
  y1: number
}

/** A chunk of document text cited as a source for an answer. */
export interface SourceChunk {
  /** Database id of the chunk. */
  id: number
  /** Text content of the chunk. */
  text: string
  /** Page numbers this chunk appears on. */
  page_numbers: number[]
  /** Bounding boxes for highlights on each page, if available. */
  bbox?: BBox[]
}

/** A single message in a chat session. */
interface HistoryMessage {
  /** Message sender role. */
  role: 'user' | 'assistant'
  /** Message text content. */
  content: string
  /** Source chunks cited by an assistant message. */
  source_chunks?: SourceChunk[]
}

/** The response body returned by the chat endpoint. */
export interface ChatResponse {
  /** The assistant's answer text. */
  answer: string
  /** Source chunks that support the answer. */
  source_chunks?: SourceChunk[]
}

// ── Endpoints ──────────────────────────────────────────────────────

/**
 * Retrieve the full chat history for a document.
 *
 * @param documentId - Document UUID.
 * @returns Promise resolving to an object with a messages array.
 */
export async function getChatHistory(documentId: string): Promise<{ messages: HistoryMessage[] }> {
  try {
    return await apiFetch<{ messages: HistoryMessage[] }>(`/api/documents/${documentId}/chat/history`)
  } catch {
    return { messages: [] }
  }
}

/**
 * Send a user question and receive the assistant's answer with sources.
 *
 * @param documentId - Document UUID.
 * @param question   - The user's question text.
 * @returns Promise resolving to the chat response.
 * @throws {ApiError} On request failure or if the document is not ready.
 */
export async function postChatMessage(documentId: string, question: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>(`/api/documents/${documentId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
}
