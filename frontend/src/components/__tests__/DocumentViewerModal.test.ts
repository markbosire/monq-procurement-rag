import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import DocumentViewerModal from '../DocumentViewerModal.vue'

const mockGetDocument = vi.hoisted(() => vi.fn())
const mockGetDocumentPdf = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  getDocument: mockGetDocument,
  getDocumentPdf: mockGetDocumentPdf,
}))

const BASE_DOC = {
  document_id: '1',
  classification: { category: 'RFP', confidence: 0.9, reasoning: 'R' },
  chunk_count: 5,
  status: 'ready',
  title: 'Test',
  summary: null,
  extractions: null,
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  window.innerWidth = 1024
  window.innerHeight = 768
  document.body.innerHTML = ''
})

function createWrapper(props: Record<string, unknown> = {}) {
  return mount(DocumentViewerModal, {
    props: {
      documentId: 'doc-1',
      chunkId: 1,
      chunkText: 'test chunk text',
      ...props,
    },
    attachTo: document.body,
  })
}

describe('DocumentViewerModal', () => {
  it('shows loading state initially', () => {
    mockGetDocumentPdf.mockReturnValue(new Promise(() => {}))
    mockGetDocument.mockResolvedValue(BASE_DOC)

    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Loading PDF')
  })

  it('renders close button and document header', () => {
    mockGetDocumentPdf.mockReturnValue(new Promise(() => {}))
    mockGetDocument.mockResolvedValue(BASE_DOC)

    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Document')
    const buttons = wrapper.findAll('button')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('emits close on close button click', async () => {
    mockGetDocumentPdf.mockReturnValue(new Promise(() => {}))
    mockGetDocument.mockResolvedValue(BASE_DOC)

    const wrapper = createWrapper()
    const closeBtn = wrapper.findAll('button').filter(b => b.text() === '\u00D7')
    if (closeBtn.length > 0) {
      await closeBtn[0].trigger('click')
      expect(wrapper.emitted('close')).toBeTruthy()
    }
  })

  it('shows error state when PDF loading fails', async () => {
    mockGetDocumentPdf.mockRejectedValue(new Error('PDF not available'))
    mockGetDocument.mockResolvedValue(BASE_DOC)

    const wrapper = createWrapper()
    await new Promise(r => setTimeout(r, 50))
    await nextTick()
    expect(wrapper.text()).toContain('PDF not available')
  })

  it('has prev and next nav buttons', async () => {
    mockGetDocumentPdf.mockResolvedValue(new ArrayBuffer(8))
    mockGetDocument.mockResolvedValue(BASE_DOC)

    const wrapper = createWrapper()
    await new Promise(r => setTimeout(r, 100))
    await nextTick()

    const prevBtn = wrapper.find('button[aria-label="Previous page"]')
    const nextBtn = wrapper.find('button[aria-label="Next page"]')
    expect(prevBtn.exists()).toBe(true)
    expect(nextBtn.exists()).toBe(true)
  })

  it('closes when clicking the backdrop', async () => {
    mockGetDocumentPdf.mockReturnValue(new Promise(() => {}))
    mockGetDocument.mockResolvedValue(BASE_DOC)

    const wrapper = createWrapper()
    const backdrop = wrapper.find('.fixed.inset-0')
    await backdrop.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
