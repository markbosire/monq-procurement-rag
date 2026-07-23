import { createMockDocumentListItem, createMockDocumentResponse, createMockSourceChunk, createMockChatMessage } from '../utils'
import type { DocumentListItem, DocumentResponse } from '../../api/documents'
import type { ChatResponse } from '../../api/chat'

function delay<T>(data: T, ms = 10): Promise<T> {
  return new Promise(r => setTimeout(r, ms)).then(() => data)
}

export function mockListDocuments(items?: DocumentListItem[]) {
  return delay(items ?? [
    createMockDocumentListItem({ document_id: 'doc-1', filename: 'contract.pdf' }),
    createMockDocumentListItem({ document_id: 'doc-2', filename: 'rfp.pdf' }),
  ])
}

export function mockGetDocument(overrides?: Partial<DocumentResponse>) {
  return delay(createMockDocumentResponse(overrides))
}

export function mockUploadDocument(overrides?: Partial<DocumentResponse>) {
  return delay(createMockDocumentResponse({
    document_id: 'new-doc',
    status: 'processing',
    ...overrides,
  }), 5)
}

export function mockPostChatMessage(overrides?: Partial<ChatResponse>) {
  return delay({
    answer: 'Based on the document, the contract value is $50,000.',
    source_chunks: [
      createMockSourceChunk({ id: 1, text: 'Contract value is $50,000.', page_numbers: [3], bbox: [{ page: 3, x0: 100, y0: 200, x1: 400, y1: 220 }] }),
      createMockSourceChunk({ id: 2, text: 'Payment terms are net 30.', page_numbers: [4], bbox: [{ page: 4, x0: 50, y0: 300, x1: 300, y1: 320 }] }),
    ],
    ...overrides,
  })
}

export function mockGetChatHistory() {
  return delay({
    messages: [
      createMockChatMessage({ role: 'user', content: 'What is the contract value?', source_chunks: [] }),
      createMockChatMessage({ role: 'assistant', content: 'The contract value is $50,000.', source_chunks: [createMockSourceChunk({ id: 1 })] }),
    ],
  })
}
