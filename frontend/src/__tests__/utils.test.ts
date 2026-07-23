import { describe, it, expect } from 'vitest'
import {
  createMockDocumentListItem,
  createMockDocumentResponse,
  createMockSourceChunk,
  createMockChatMessage,
  createMockChatResponse,
  createMockFile,
  createTestRouter,
} from './utils'

describe('mock factories', () => {
  it('createMockDocumentListItem', () => {
    const item = createMockDocumentListItem({ filename: 'custom.pdf' })
    expect(item.document_id).toBe('doc-001')
    expect(item.filename).toBe('custom.pdf')
    expect(item.category).toBe('RFP/RFQ')
  })

  it('createMockDocumentResponse', () => {
    const resp = createMockDocumentResponse({ status: 'processing' })
    expect(resp.document_id).toBe('doc-001')
    expect(resp.status).toBe('processing')
    expect(resp.classification.category).toBe('RFP/RFQ')
  })

  it('createMockSourceChunk', () => {
    const chunk = createMockSourceChunk({ id: 42 })
    expect(chunk.id).toBe(42)
    expect(chunk.page_numbers).toEqual([1, 2])
  })

  it('createMockChatMessage', () => {
    const msg = createMockChatMessage({ content: 'custom answer' })
    expect(msg.role).toBe('assistant')
    expect(msg.content).toBe('custom answer')
    expect(msg.source_chunks).toHaveLength(1)
  })

  it('createMockChatResponse', () => {
    const resp = createMockChatResponse({ answer: 'test answer' })
    expect(resp.answer).toBe('test answer')
    expect(resp.source_chunks).toHaveLength(1)
  })

  it('createMockFile', () => {
    const file = createMockFile('test.pdf')
    expect(file.name).toBe('test.pdf')
    expect(file.type).toBe('application/pdf')
    expect(file.size).toBeGreaterThan(0)
  })

  it('createTestRouter', () => {
    const router = createTestRouter()
    expect(router.hasRoute('documents')).toBe(true)
    expect(router.hasRoute('document-chat')).toBe(true)
  })
})
