import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '../useChatStore'

const mockGetDocument = vi.hoisted(() => vi.fn())
const mockGetChatHistory = vi.hoisted(() => vi.fn())
const mockPostChatMessage = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  getDocument: mockGetDocument,
}))

vi.mock('../../api/chat', () => ({
  getChatHistory: mockGetChatHistory,
  postChatMessage: mockPostChatMessage,
}))

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('useChatStore', () => {
  it('starts with empty state', () => {
    const store = useChatStore()
    expect(store.messages).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
    expect(store.documentInfo).toBeNull()
  })

  describe('loadDocumentInfo', () => {
    it('sets documentInfo from getDocument', async () => {
      const info = { document_id: '1', classification: { category: 'C', confidence: 0.9, reasoning: 'R' }, chunk_count: 3, title: 'T', summary: 'S', extractions: null }
      mockGetDocument.mockResolvedValue(info)
      const store = useChatStore()
      await store.loadDocumentInfo('1')
      expect(mockGetDocument).toHaveBeenCalledWith('1')
      expect(store.documentInfo).toEqual(info)
    })

    it('does not set error on failure', async () => {
      mockGetDocument.mockRejectedValue(new Error('Not found'))
      const store = useChatStore()
      await store.loadDocumentInfo('1')
      expect(store.documentInfo).toBeNull()
      expect(store.error).toBeNull()
    })
  })

  describe('loadHistory', () => {
    it('sets messages from getChatHistory', async () => {
      const history = { messages: [{ role: 'user' as const, content: 'hi', source_chunks: [] }] }
      mockGetChatHistory.mockResolvedValue(history)
      const store = useChatStore()
      await store.loadHistory('1')
      expect(mockGetChatHistory).toHaveBeenCalledWith('1')
      expect(store.messages).toHaveLength(1)
      expect(store.messages[0].role).toBe('user')
    })

    it('resets messages on failure', async () => {
      mockGetChatHistory.mockRejectedValue(new Error('Network error'))
      const store = useChatStore()
      await store.loadHistory('1')
      expect(store.messages).toEqual([])
    })
  })

  describe('send', () => {
    it('appends user message and assistant response', async () => {
      mockPostChatMessage.mockResolvedValue({ answer: 'test answer', source_chunks: [] })
      const store = useChatStore()
      await store.send('1', 'What is this?')
      expect(store.messages).toHaveLength(2)
      expect(store.messages[0].role).toBe('user')
      expect(store.messages[0].content).toBe('What is this?')
      expect(store.messages[1].role).toBe('assistant')
      expect(store.messages[1].content).toBe('test answer')
      expect(store.loading).toBe(false)
    })

    it('sets error on failure', async () => {
      mockPostChatMessage.mockRejectedValue(new Error('Chat error'))
      const store = useChatStore()
      await store.send('1', 'question')
      expect(store.error).toBe('Chat error')
      expect(store.loading).toBe(false)
      expect(store.messages).toHaveLength(1)
    })
  })
})
