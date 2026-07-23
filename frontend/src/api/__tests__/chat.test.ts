import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getChatHistory, postChatMessage } from '../chat'
import * as apiClient from '../apiClient'

vi.mock('../apiClient', () => ({
  apiFetch: vi.fn(),
}))

const mockApiFetch = vi.mocked(apiClient.apiFetch)

beforeEach(() => {
  vi.clearAllMocks()
})

describe('getChatHistory', () => {
  it('calls /api/documents/{id}/chat/history', async () => {
    const history = { messages: [{ role: 'user', content: 'hello' }] }
    mockApiFetch.mockResolvedValue(history)
    const result = await getChatHistory('doc-1')
    expect(mockApiFetch).toHaveBeenCalledWith('/api/documents/doc-1/chat/history')
    expect(result).toEqual(history)
  })

  it('returns empty messages on fetch failure', async () => {
    mockApiFetch.mockRejectedValue(new Error('Network error'))
    const result = await getChatHistory('doc-1')
    expect(result).toEqual({ messages: [] })
  })
})

describe('postChatMessage', () => {
  it('POSTs question to /api/documents/{id}/chat', async () => {
    const response = { answer: 'test answer', source_chunks: [{ id: 1, text: 'source', page_numbers: [1] }] }
    mockApiFetch.mockResolvedValue(response)
    const result = await postChatMessage('doc-1', 'What is this?')
    expect(mockApiFetch).toHaveBeenCalledWith('/api/documents/doc-1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: 'What is this?' }),
    })
    expect(result).toEqual(response)
  })
})
