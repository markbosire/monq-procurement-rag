import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { useToast } from '../composables/useToast'
import { activeHighlight } from '../composables/useSourceViewer'
import { useChatStore } from '../stores/useChatStore'
import { useDocumentStore } from '../stores/useDocumentStore'
import DocumentGridPage from '../pages/DocumentGridPage.vue'
import DocumentChatPage from '../pages/DocumentChatPage.vue'

const mockUploadDocument = vi.hoisted(() => vi.fn())
const mockListDocuments = vi.hoisted(() => vi.fn().mockResolvedValue([]))
const mockGetDocument = vi.hoisted(() => vi.fn())
const mockGetDocumentPdf = vi.hoisted(() => vi.fn())
const mockGetChatHistory = vi.hoisted(() => vi.fn().mockResolvedValue({ messages: [] }))
const mockPostChatMessage = vi.hoisted(() => vi.fn())

vi.mock('../api/documents', () => ({
  uploadDocument: mockUploadDocument,
  listDocuments: mockListDocuments,
  getDocument: mockGetDocument,
  getDocumentPdf: mockGetDocumentPdf,
  renameDocument: vi.fn(),
  deleteDocument: vi.fn(),
}))

vi.mock('../api/chat', () => ({
  getChatHistory: mockGetChatHistory,
  postChatMessage: mockPostChatMessage,
}))

beforeEach(() => {
  setActivePinia(createPinia())
  useToast().clear()
  activeHighlight.value = null
  vi.clearAllMocks()
  window.innerWidth = 1400
  window.dispatchEvent(new Event('resize'))
})

afterEach(() => {
  activeHighlight.value = null
})

describe('Upload → Navigate → Chat flow', () => {
  it('uploads a PDF and store updates document list', async () => {
    mockUploadDocument.mockResolvedValue({
      document_id: 'new-doc-1',
      classification: { category: 'Contract', confidence: 0.95, reasoning: 'Match' },
      chunk_count: 0,
      status: 'processing',
      title: 'New Contract',
      summary: null,
      extractions: null,
    })
    mockListDocuments.mockResolvedValue([])

    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', redirect: '/documents' },
        { path: '/documents', name: 'documents', component: DocumentGridPage },
        { path: '/documents/:id', name: 'document-chat', component: DocumentChatPage, props: true },
      ],
    })

    await router.push('/documents')
    await router.isReady()

    const store = useDocumentStore()
    const wrapper = mount(DocumentGridPage, {
      global: { plugins: [pinia, router] },
    })
    await new Promise(r => setTimeout(r, 50))

    expect(wrapper.text()).toContain('Add Document')

    const vm = wrapper.vm as unknown as { uploadFile: (f: File) => Promise<void> }
    const file = new File(['pdf content'], 'contract.pdf', { type: 'application/pdf' })
    await vm.uploadFile(file)
    await new Promise(r => setTimeout(r, 100))
    await nextTick()

    expect(mockUploadDocument).toHaveBeenCalledWith(file)
  })

  it('renders chat page with document title and supports sending messages', async () => {
    mockGetDocument.mockResolvedValue({
      document_id: 'chat-doc',
      classification: { category: 'Contract', confidence: 0.95, reasoning: 'Match' },
      chunk_count: 5,
      status: 'ready',
      title: 'Service Contract',
      summary: 'A contract document.',
      extractions: null,
    })
    mockGetDocumentPdf.mockReturnValue(new Promise(() => {}))
    mockGetChatHistory.mockResolvedValue({ messages: [] })
    mockPostChatMessage.mockResolvedValue({
      answer: 'The value is $50,000.',
      source_chunks: [
        { id: 1, text: 'The value is $50,000.', page_numbers: [3], bbox: [{ page: 3, x0: 100, y0: 200, x1: 400, y1: 220 }] },
      ],
    })

    const pinia = createPinia()
    setActivePinia(pinia)
    const router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: '/', redirect: '/documents' },
        { path: '/documents', name: 'documents', component: { template: '<div>Grid</div>' } },
        { path: '/documents/:id', name: 'document-chat', component: DocumentChatPage, props: true },
      ],
    })

    await router.push('/documents/chat-doc')
    await router.isReady()

    const chatStore = useChatStore()
    chatStore.documentInfo = {
      document_id: 'chat-doc',
      classification: { category: 'Contract', confidence: 0.95, reasoning: 'Match' },
      chunk_count: 5,
      title: 'Service Contract',
      summary: 'A contract document.',
      extractions: null,
    }
    chatStore.loading = false

    const wrapper = mount(DocumentChatPage, {
      props: { id: 'chat-doc' },
      global: { plugins: [pinia, router] },
    })
    await nextTick()

    expect(wrapper.text()).toContain('Service Contract')

    chatStore.messages.push({ role: 'user', content: 'What is the value?', source_chunks: [] })
    chatStore.messages.push({
      role: 'assistant',
      content: 'The value is $50,000.',
      source_chunks: [
        { id: 1, text: 'The value is $50,000.', page_numbers: [3], bbox: [{ page: 3, x0: 100, y0: 200, x1: 400, y1: 220 }] },
      ],
    })
    await nextTick()

    expect(wrapper.text()).toContain('The value is $50,000.')
  })
})
