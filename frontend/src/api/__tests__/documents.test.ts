import { describe, it, expect, vi, beforeEach } from 'vitest'
import { listDocuments, getDocument, uploadDocument, renameDocument, deleteDocument, getDocumentPdf } from '../documents'
import * as apiClient from '../apiClient'

vi.mock('../apiClient', () => ({
  apiFetch: vi.fn(),
  apiFetchRaw: vi.fn(),
}))

const mockApiFetch = vi.mocked(apiClient.apiFetch)
const mockApiFetchRaw = vi.mocked(apiClient.apiFetchRaw)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('listDocuments', () => {
  it('calls /api/documents and returns list', async () => {
    const docs = [{ document_id: '1', filename: 'a.pdf', category: 'Contract', chunk_count: 3, title: 'A', created_at: null }]
    mockApiFetch.mockResolvedValue(docs)
    const result = await listDocuments()
    expect(mockApiFetch).toHaveBeenCalledWith('/api/documents')
    expect(result).toEqual(docs)
  })
})

describe('getDocument', () => {
  it('calls /api/documents/{id} and returns document', async () => {
    const doc = { document_id: '1', classification: { category: 'C', confidence: 0.9, reasoning: 'R' }, chunk_count: 3, status: 'ready', title: null, summary: null, extractions: null }
    mockApiFetch.mockResolvedValue(doc)
    const result = await getDocument('1')
    expect(mockApiFetch).toHaveBeenCalledWith('/api/documents/1')
    expect(result).toEqual(doc)
  })
})

describe('uploadDocument', () => {
  it('POSTs FormData to /api/documents', async () => {
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    const response = { document_id: '2', classification: { category: 'RFP', confidence: 0.8, reasoning: 'R' }, chunk_count: 0, status: 'processing', title: null, summary: null, extractions: null }
    mockApiFetch.mockResolvedValue(response)
    const result = await uploadDocument(file)
    expect(mockApiFetch).toHaveBeenCalledWith('/api/documents', { method: 'POST', body: expect.any(FormData) })
    const callBody = mockApiFetch.mock.calls[0][1]?.body as FormData
    expect(callBody.get('file')).toBe(file)
    expect(result).toEqual(response)
  })
})

describe('renameDocument', () => {
  it('PATCHes filename to /api/documents/{id}', async () => {
    const response = { document_id: '1', classification: { category: 'C', confidence: 0.9, reasoning: 'R' }, chunk_count: 3, status: 'ready', title: null, summary: null, extractions: null }
    mockApiFetch.mockResolvedValue(response)
    const result = await renameDocument('1', 'newname.pdf')
    expect(mockApiFetch).toHaveBeenCalledWith('/api/documents/1', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: 'newname.pdf' }),
    })
    expect(result).toEqual(response)
  })
})

describe('deleteDocument', () => {
  it('DELETEs /api/documents/{id}', async () => {
    mockApiFetchRaw.mockResolvedValue(new Response())
    await deleteDocument('1')
    expect(mockApiFetchRaw).toHaveBeenCalledWith('/api/documents/1', { method: 'DELETE' })
  })
})

describe('getDocumentPdf', () => {
  it('fetches PDF and returns ArrayBuffer', async () => {
    const buffer = new ArrayBuffer(8)
    mockApiFetchRaw.mockResolvedValue({ arrayBuffer: () => Promise.resolve(buffer) } as Response)
    const result = await getDocumentPdf('1')
    expect(mockApiFetchRaw).toHaveBeenCalledWith('/api/documents/1/pdf')
    expect(result).toBeInstanceOf(ArrayBuffer)
  })
})
