import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDocumentStore } from '../useDocumentStore'
import { createMockDocumentListItem } from '../../__tests__/utils'

const mockListDocuments = vi.hoisted(() => vi.fn())
const mockUploadDocument = vi.hoisted(() => vi.fn())
const mockRenameDocument = vi.hoisted(() => vi.fn())
const mockDeleteDocument = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  listDocuments: mockListDocuments,
  uploadDocument: mockUploadDocument,
  renameDocument: mockRenameDocument,
  deleteDocument: mockDeleteDocument,
}))

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useDocumentStore', () => {
  it('starts with empty state', () => {
    const store = useDocumentStore()
    expect(store.documents).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.uploading).toBe(false)
    expect(store.error).toBeNull()
  })

  describe('fetchAll', () => {
    it('sets documents from api.listDocuments', async () => {
      const docs = [createMockDocumentListItem()]
      mockListDocuments.mockResolvedValue(docs)
      const store = useDocumentStore()
      await store.fetchAll()
      expect(mockListDocuments).toHaveBeenCalledOnce()
      expect(store.documents).toEqual(docs)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('sets error on failure', async () => {
      mockListDocuments.mockRejectedValue(new Error('Network error'))
      const store = useDocumentStore()
      await store.fetchAll()
      expect(store.documents).toEqual([])
      expect(store.loading).toBe(false)
      expect(store.error).toBe('Network error')
    })
  })

  describe('upload', () => {
    it('uploads file, refreshes list, returns document', async () => {
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
      const uploadResponse = { document_id: '2', classification: { category: 'RFP', confidence: 0.8, reasoning: 'R' }, chunk_count: 0, status: 'processing', title: null, summary: null, extractions: null }
      mockUploadDocument.mockResolvedValue(uploadResponse)
      mockListDocuments.mockResolvedValue([])
      const store = useDocumentStore()
      const result = await store.upload(file)
      expect(mockUploadDocument).toHaveBeenCalledWith(file)
      expect(mockListDocuments).toHaveBeenCalledOnce()
      expect(result).toEqual(uploadResponse)
      expect(store.uploading).toBe(false)
    })

    it('sets error on upload failure', async () => {
      mockUploadDocument.mockRejectedValue(new Error('Upload failed'))
      const store = useDocumentStore()
      const result = await store.upload(new File([''], 'test.pdf', { type: 'application/pdf' }))
      expect(result).toBeNull()
      expect(store.error).toBe('Upload failed')
      expect(store.uploading).toBe(false)
    })
  })

  describe('rename', () => {
    it('renames and refreshes list', async () => {
      mockRenameDocument.mockResolvedValue({} as never)
      mockListDocuments.mockResolvedValue([])
      const store = useDocumentStore()
      const result = await store.rename('1', 'new.pdf')
      expect(mockRenameDocument).toHaveBeenCalledWith('1', 'new.pdf')
      expect(result).toBe(true)
    })

    it('returns false on failure', async () => {
      mockRenameDocument.mockRejectedValue(new Error('Not found'))
      const store = useDocumentStore()
      const result = await store.rename('1', 'new.pdf')
      expect(result).toBe(false)
      expect(store.error).toBe('Not found')
    })
  })

  describe('remove', () => {
    it('deletes document and removes from local list', async () => {
      mockDeleteDocument.mockResolvedValue(undefined)
      const store = useDocumentStore()
      store.documents = [createMockDocumentListItem({ document_id: '1' })]
      const result = await store.remove('1')
      expect(mockDeleteDocument).toHaveBeenCalledWith('1')
      expect(result).toBe(true)
      expect(store.documents).toEqual([])
    })

    it('returns false on failure', async () => {
      mockDeleteDocument.mockRejectedValue(new Error('Forbidden'))
      const store = useDocumentStore()
      const result = await store.remove('1')
      expect(result).toBe(false)
      expect(store.error).toBe('Forbidden')
    })
  })
})
