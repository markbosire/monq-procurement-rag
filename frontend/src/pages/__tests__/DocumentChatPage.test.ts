import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { nextTick } from 'vue'
import DocumentChatPage from '../DocumentChatPage.vue'
import { activeHighlight } from '../../composables/useSourceViewer'
import { useChatStore } from '../../stores/useChatStore'

const mockGetDocument = vi.hoisted(() => vi.fn())
const mockGetChatHistory = vi.hoisted(() => vi.fn().mockResolvedValue({ messages: [] }))
const mockPostChatMessage = vi.hoisted(() => vi.fn())
const mockGetDocumentPdf = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  getDocument: mockGetDocument,
  getDocumentPdf: mockGetDocumentPdf,
}))

vi.mock('../../api/chat', () => ({
  getChatHistory: mockGetChatHistory,
  postChatMessage: mockPostChatMessage,
}))

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/documents' },
      { path: '/documents', component: { template: '<div>Grid</div>' } },
      { path: '/documents/:id', component: { template: '<div>Chat</div>' } },
    ],
  })
}

beforeEach(() => {
  activeHighlight.value = null
  vi.clearAllMocks()
})

afterEach(() => {
  activeHighlight.value = null
})

function createMountedPage(props: Record<string, unknown> = {}, width = 1400) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createTestRouter()
  window.innerWidth = width
  window.dispatchEvent(new Event('resize'))
  const wrapper = mount(DocumentChatPage, {
    props: { id: 'doc-1', ...props },
    global: { plugins: [pinia, router] },
  })
  return { wrapper, pinia, router }
}

describe('DocumentChatPage', () => {
  it('renders header with back button', () => {
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })
    const { wrapper } = createMountedPage()
    expect(wrapper.find('header').exists()).toBe(true)
  })

  it('shows Loading... when no document info', () => {
    mockGetDocument.mockReturnValue(new Promise(() => {}))
    const { wrapper } = createMountedPage()
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows document title when loaded', async () => {
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc Title',
      summary: 'A summary.',
      extractions: null,
    })
    const { wrapper } = createMountedPage()
    await new Promise(r => setTimeout(r, 50))
    expect(wrapper.text()).toContain('Test Doc Title')
  })

  it('shows PDF button on small screens when document is loaded', async () => {
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })
    const { wrapper } = createMountedPage({}, 800)
    await new Promise(r => setTimeout(r, 50))

    const pdfBtns = wrapper.findAll('button').filter(b => b.text().trim() === 'PDF')
    expect(pdfBtns.length).toBeGreaterThan(0)
  })

  it('shows side-by-side layout on large screens', async () => {
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })

    const chatStore = useChatStore()
    chatStore.documentInfo = {
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    }

    const { wrapper } = createMountedPage({}, 1400)
    await new Promise(r => setTimeout(r, 100))
    await nextTick()

    const mainEls = wrapper.findAll('main')
    expect(mainEls.length).toBeGreaterThan(0)
  })

  it('does not show PDF modal by default on small screens', async () => {
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })

    const chatStore = useChatStore()
    chatStore.documentInfo = {
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    }

    const { wrapper } = createMountedPage({}, 800)
    await new Promise(r => setTimeout(r, 100))
    await nextTick()

    expect(wrapper.text()).not.toContain('Document PDF')
  })

  it('responds to window resize events', async () => {
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })

    const chatStore = useChatStore()
    chatStore.documentInfo = {
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    }

    const { wrapper } = createMountedPage({}, 1400)
    await new Promise(r => setTimeout(r, 50))

    window.innerWidth = 800
    window.dispatchEvent(new Event('resize'))
    await nextTick()
    await new Promise(r => setTimeout(r, 50))
  })
})
